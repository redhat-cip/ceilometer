# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Steven Berler <steven.berler@dreamhost.com>
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
"""Test getting the max resource volume.
"""

import datetime

from ceilometer.publisher import utils
from ceilometer import sample

from ceilometer.tests import api as tests_api
from ceilometer.tests import db as tests_db


class TestMaxResourceVolume(tests_api.TestBase,
                            tests_db.MixinTestsWithBackendScenarios):

    def setUp(self):
        super(TestMaxResourceVolume, self).setUp()
        for i in range(3):
            s = sample.Sample(
                'volume.size',
                'gauge',
                'GiB',
                5 + i,
                'user-id',
                'project1',
                'resource-id',
                timestamp=datetime.datetime(2012, 9, 25, 10 + i, 30 + i),
                resource_metadata={'display_name': 'test-volume',
                                   'tag': 'self.sample',
                                   },
                source='source1',
            )
            msg = utils.meter_message_from_counter(
                s,
                self.CONF.publisher.metering_secret,
            )
            self.collector_conn.record_metering_data(msg)

    def test_no_time_bounds(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max')
        expected = {'volume': 7}
        self.assertEqual(expected, data)

    def test_no_time_bounds_non_admin(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        headers={"X-Roles": "Member",
                                 "X-Project-Id": "project1"})
        self.assertEqual({'volume': 7}, data)

    def test_no_time_bounds_wrong_tenant(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        headers={"X-Roles": "Member",
                                 "X-Project-Id": "??"})
        self.assertEqual({'volume': None}, data)

    def test_start_timestamp(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        start_timestamp='2012-09-25T11:30:00')
        expected = {'volume': 7}
        self.assertEqual(expected, data)

    def test_start_timestamp_after(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        start_timestamp='2012-09-25T12:34:00')
        expected = {'volume': None}
        self.assertEqual(expected, data)

    def test_end_timestamp(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        end_timestamp='2012-09-25T11:30:00')
        expected = {'volume': 5}
        self.assertEqual(expected, data)

    def test_end_timestamp_before(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        end_timestamp='2012-09-25T09:54:00')
        expected = {'volume': None}
        self.assertEqual(expected, data)

    def test_start_end_timestamp(self):
        data = self.get('/resources/resource-id/meters/volume.size/volume/max',
                        start_timestamp='2012-09-25T11:30:00',
                        end_timestamp='2012-09-25T11:32:00')
        expected = {'volume': 6}
        self.assertEqual(expected, data)
