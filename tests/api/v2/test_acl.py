# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Julien Danjou <julien@danjou.info>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Test ACL."""

import datetime
from mock import patch

from oslo.config import cfg

from ceilometer.api import acl
from ceilometer import policy
from ceilometer.openstack.common import jsonutils

from .base import FunctionalTest

VALID_TOKEN = '4562138218392831'
VALID_TOKEN2 = '4562138218392832'


class FakeMemcache(object):
    def __init__(self):
        self.set_key = None
        self.set_value = None
        self.token_expiration = None

    def get(self, key):
        if key == "tokens/%s" % VALID_TOKEN:
            dt = datetime.datetime.now() + datetime.timedelta(minutes=5)
            return jsonutils.dumps(({'access': {
                'token': {'id': VALID_TOKEN},
                'user': {
                    'id': 'user_id1',
                    'name': 'user_name1',
                    'tenantId': 'bc23a9d531064583ace8f67dad60f6bb',
                    'tenantName': 'admin',
                    'roles': [
                        {'name': 'admin'},
                        {'name': '_member_'},
                        {'name': 'ResellerAdmin'},
                    ]},
            }}, dt.strftime("%s")))
        if key == "tokens/%s" % VALID_TOKEN2:
            dt = datetime.datetime.now() + datetime.timedelta(minutes=5)
            return jsonutils.dumps(({'access': {
                'token': {'id': VALID_TOKEN2},
                'user': {
                    'id': 'user_id1',
                    'name': 'test',
                    'tenantId': '52196e190ce44e53817c9c55b2b965ac',
                    'tenantName': 'test',
                    'roles': [
                        {'name': 'Member'},
                        {'name': '_member_'},
                        {'name': 'ResellerAdmin'},
                    ]},
            }}, dt.strftime("%s")))

    def set(self, key, value, time=None):
        self.set_value = value
        self.set_key = key


class TestAPIACL(FunctionalTest):

    def setUp(self):
        super(TestAPIACL, self).setUp()
        self.environ = {'fake.cache': FakeMemcache()}

    def get_json(self, path, expect_errors=False, headers=None,
                 q=[], **params):
        return super(TestAPIACL, self).get_json(path,
                                                expect_errors=expect_errors,
                                                headers=headers,
                                                q=q,
                                                extra_environ=self.environ,
                                                **params)

    def _make_app(self):
        cfg.CONF.set_override("cache", "fake.cache", group=acl.OPT_GROUP_NAME)
        return super(TestAPIACL, self)._make_app(enable_acl=True)

    def test_non_authenticated(self):
        response = self.get_json('/meters', expect_errors=True)
        self.assertEqual(response.status_int, 401)

    def test_authenticated_wrong_role(self):
        response = self.get_json('/meters',
                                 expect_errors=True,
                                 headers={
                                     "X-Roles": "Member",
                                     "X-Tenant-Name": "admin",
                                     "X-Tenant-Id":
                                     "bc23a9d531064583ace8f67dad60f6bb",
                                 })
        self.assertEqual(response.status_int, 401)

    # FIXME(dhellmann): This test is not properly looking at the tenant
    # info. We do not correctly detect the improper tenant. That's
    # really something the keystone middleware would have to do using
    # the incoming token, which we aren't providing.
    #
    # def test_authenticated_wrong_tenant(self):
    #     response = self.get_json('/sources',
    #                              expect_errors=True,
    #                              headers={
    #             "X-Roles": "admin",
    #             "X-Tenant-Name": "achoo",
    #             "X-Tenant-Id": "bc23a9d531064583ace8f67dad60f6bb",
    #             })
    #     self.assertEqual(response.status_int, 401)

    def test_authenticated(self):
        response = self.get_json('/meters',
                                 expect_errors=True,
                                 headers={
                                     "X-Auth-Token": VALID_TOKEN,
                                     "X-Roles": "admin,_member_,ResellerAdmin",
                                     "X-Tenant-Name": "admin",
                                     "X-Tenant-Id":
                                     "bc23a9d531064583ace8f67dad60f6bb",
                                 })
        self.assertEqual(response.status_int, 200)

    def test_post_alarm_multiple_role_admin(self):
        json = {
            'name': 'added_alarm',
            'counter_name': 'ameter',
            'comparison_operator': 'gt',
            'threshold': 2.0,
            'statistic': 'average',
            'matching_metadata': {'project_id':
                                  '7bcc0e4e191c11e39c4800224d8226cd'}
        }
        with patch('ceilometer.openstack.common.rpc.cast'):
            response = self.post_json('/alarms', params=json,
                                      expect_errors=True,
                                      extra_environ=self.environ,
                                      headers={
                                          "X-Auth-Token": VALID_TOKEN,
                                          "X-Roles":
                                          "admin,_member_,ResellerAdmin",
                                          "X-Tenant-Name": "admin",
                                          "X-Tenant-Id":
                                          "bc23a9d531064583ace8f67dad60f6bb",
                                      })
            self.assertEqual(response.status_int, 200)
        alarms = list(self.alarm_conn.alarm_list())
        self.assertEqual(1, len(alarms))
        self.assertEqual(alarms[0].matching_metadata['project_id'],
                         '7bcc0e4e191c11e39c4800224d8226cd')

    def test_post_alarm_multiple_role_not_admin(self):
        json = {
            'name': 'added_alarm',
            'counter_name': 'ameter',
            'comparison_operator': 'gt',
            'threshold': 2.0,
            'statistic': 'average',
            'matching_metadata': {'project_id':
                                  '7bcc0e4e191c11e39c4800224d8226cd'}
        }
        with patch('ceilometer.openstack.common.rpc.cast'):
            response = self.post_json('/alarms', params=json,
                                      expect_errors=True,
                                      extra_environ=self.environ,
                                      headers={
                                          "X-Auth-Token": VALID_TOKEN2,
                                          "X-Roles": "_member_",
                                          "X-Tenant-Name": "test",
                                          "X-Tenant-Id":
                                          "52196e190ce44e53817c9c55b2b965ac",
                                      })
            self.assertEqual(response.status_int, 401)
