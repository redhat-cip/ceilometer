# -*- encoding: utf-8 -*-
#
# Copyright © 2013 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
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

import datetime

from ceilometer.alarm.storage import models as alarm_models
from ceilometer.event.storage import models as event_models
from ceilometer.collector.storage import models as collector_models
from ceilometer.openstack.common import test
from ceilometer.storage import base


class FakeModel(base.Model):
    def __init__(self, arg1, arg2):
        base.Model.__init__(self, arg1=arg1, arg2=arg2)


class ModelTest(test.BaseTestCase):

    def test_create_attributes(self):
        m = FakeModel(1, 2)
        self.assertEqual(1, m.arg1)
        self.assertEqual(2, m.arg2)

    def test_as_dict(self):
        m = FakeModel(1, 2)
        d = m.as_dict()
        self.assertEqual({'arg1': 1, 'arg2': 2}, d)

    def test_as_dict_recursive(self):
        m = FakeModel(1, FakeModel('a', 'b'))
        d = m.as_dict()
        self.assertEqual({'arg1': 1,
                          'arg2': {'arg1': 'a',
                                   'arg2': 'b'}},
                         d)

    def test_as_dict_recursive_list(self):
        m = FakeModel(1, [FakeModel('a', 'b')])
        d = m.as_dict()
        self.assertEqual({'arg1': 1,
                          'arg2': [{'arg1': 'a',
                                    'arg2': 'b'}]},
                         d)

    def test_event_repr_no_traits(self):
        x = event_models.Event("1", "name", "now", None)
        self.assertEqual("<Event: 1, name, now, >", repr(x))

    def test_get_field_names_of_sample(self):
        sample_fields = ["source", "counter_name", "counter_type",
                         "counter_unit", "counter_volume", "user_id",
                         "project_id", "resource_id", "timestamp",
                         "resource_metadata", "message_id",
                         "message_signature", "recorded_at"]

        self.assertEqual(set(sample_fields),
                         set(collector_models.Sample.get_field_names()))

    def test_get_field_names_of_alarm(self):
        alarm_fields = ["alarm_id", "type", "enabled", "name", "description",
                        "timestamp", "user_id", "project_id", "state",
                        "state_timestamp", "ok_actions", "alarm_actions",
                        "insufficient_data_actions", "repeat_actions", "rule",
                        "time_constraints"]

        self.assertEqual(set(alarm_fields),
                         set(alarm_models.Alarm.get_field_names()))

    def test_get_field_names_of_alarmchange(self):
        alarmchange_fields = ["event_id", "alarm_id", "type", "detail",
                              "user_id", "project_id", "on_behalf_of",
                              "timestamp"]

        self.assertEqual(set(alarmchange_fields),
                         set(alarm_models.AlarmChange.get_field_names()))


class TestTraitModel(test.BaseTestCase):

    def test_convert_value(self):
        v = event_models.Trait.convert_value(
            event_models.Trait.INT_TYPE, '10')
        self.assertEqual(10, v)
        self.assertIsInstance(v, int)
        v = event_models.Trait.convert_value(
            event_models.Trait.FLOAT_TYPE, '10')
        self.assertEqual(10.0, v)
        self.assertIsInstance(v, float)

        v = event_models.Trait.convert_value(
            event_models.Trait.DATETIME_TYPE, '2013-08-08 21:05:37.123456')
        self.assertEqual(datetime.datetime(2013, 8, 8, 21, 5, 37, 123456), v)
        self.assertIsInstance(v, datetime.datetime)

        v = event_models.Trait.convert_value(
            event_models.Trait.TEXT_TYPE, 10)
        self.assertEqual("10", v)
        self.assertIsInstance(v, str)
