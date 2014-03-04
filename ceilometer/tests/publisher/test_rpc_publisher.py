# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
#
# Author: Doug Hellmann <doug.hellmann@dreamhost.com>
#         Julien Danjou <julien@danjou.info>
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
"""Tests for ceilometer/publisher/rpc.py
"""
import datetime

import eventlet
import mock
import oslo.messaging

from ceilometer import messaging
from ceilometer.openstack.common.fixture import config
from ceilometer.openstack.common import network_utils
from ceilometer.openstack.common import test
from ceilometer.publisher import rpc
from ceilometer import sample


class TestPublish(test.BaseTestCase):
    test_data = [
        sample.Sample(
            name='test',
            type=sample.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        sample.Sample(
            name='test',
            type=sample.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        sample.Sample(
            name='test2',
            type=sample.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        sample.Sample(
            name='test2',
            type=sample.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
        sample.Sample(
            name='test3',
            type=sample.TYPE_CUMULATIVE,
            unit='',
            volume=1,
            user_id='test',
            project_id='test',
            resource_id='test_run_tasks',
            timestamp=datetime.datetime.utcnow().isoformat(),
            resource_metadata={'name': 'TestPublish'},
        ),
    ]

    def setUp(self):
        super(TestPublish, self).setUp()
        self.CONF = self.useFixture(config.Config()).conf

        messaging.setup('fake://')
        self.addCleanup(messaging.cleanup)

        self.published = []

    def test_published(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://'))

        cast_context = mock.MagicMock()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.return_value = cast_context
            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)

        prepare.assert_called_once_with(
            topic=self.CONF.publisher_rpc.metering_topic)
        cast_context.cast.assert_called_once_with(
            mock.ANY, 'record_metering_data', data=mock.ANY)

    def test_publish_target(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?target=custom_procedure_call'))

        cast_context = mock.MagicMock()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.return_value = cast_context
            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)

        prepare.assert_called_once_with(
            topic=self.CONF.publisher_rpc.metering_topic)
        cast_context.cast.assert_called_once_with(
            mock.ANY, 'custom_procedure_call', data=mock.ANY)

    def test_published_with_per_meter_topic(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?per_meter_topic=1'))

        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)

            class MeterGroupMatcher(object):
                def __eq__(self, meters):
                    return len(set(meter['counter_name']
                                   for meter in meters)) == 1

            topic = self.CONF.publisher_rpc.metering_topic
            expected = [mock.call(topic=topic),
                        mock.call().cast(mock.ANY, 'record_metering_data',
                                         data=mock.ANY),
                        mock.call(topic=topic + '.test'),
                        mock.call().cast(mock.ANY, 'record_metering_data',
                                         data=MeterGroupMatcher()),
                        mock.call(topic=topic + '.test2'),
                        mock.call().cast(mock.ANY, 'record_metering_data',
                                         data=MeterGroupMatcher()),
                        mock.call(topic=topic + '.test3'),
                        mock.call().cast(mock.ANY, 'record_metering_data',
                                         data=MeterGroupMatcher())]
            self.assertEqual(prepare.mock_calls, expected)

    def test_published_concurrency(self):
        """This test the concurrent access to the local queue
        of the rpc publisher
        """

        publisher = rpc.RPCPublisher(network_utils.urlsplit('rpc://'))
        cast_context = mock.MagicMock()

        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            def fake_prepare_go(topic):
                return cast_context

            def fake_prepare_wait(topic):
                prepare.side_effect = fake_prepare_go
                # Sleep to simulate concurrency and allow other threads to work
                eventlet.sleep(0)
                return cast_context

            prepare.side_effect = fake_prepare_wait

            job1 = eventlet.spawn(publisher.publish_samples,
                                  mock.MagicMock(), self.test_data)
            job2 = eventlet.spawn(publisher.publish_samples,
                                  mock.MagicMock(), self.test_data)

            job1.wait()
            job2.wait()

        self.assertEqual(publisher.policy, 'default')
        self.assertEqual(len(cast_context.cast.mock_calls), 2)
        self.assertEqual(len(publisher.local_queue), 0)

    @mock.patch('ceilometer.publisher.rpc.LOG')
    def test_published_with_no_policy(self, mylog):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://'))
        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect

            self.assertRaises(
                oslo.messaging.MessagingDisconnected,
                publisher.publish_samples,
                mock.MagicMock(), self.test_data)
            self.assertTrue(mylog.info.called)
            self.assertEqual(publisher.policy, 'default')
            self.assertEqual(len(publisher.local_queue), 0)
            prepare.assert_called_once_with(
                topic=self.CONF.publisher_rpc.metering_topic)

    @mock.patch('ceilometer.publisher.rpc.LOG')
    def test_published_with_policy_block(self, mylog):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=default'))
        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect
            self.assertRaises(
                oslo.messaging.MessagingDisconnected,
                publisher.publish_samples,
                mock.MagicMock(), self.test_data)
            self.assertTrue(mylog.info.called)
            self.assertEqual(len(publisher.local_queue), 0)
            prepare.assert_called_once_with(
                topic=self.CONF.publisher_rpc.metering_topic)

    @mock.patch('ceilometer.publisher.rpc.LOG')
    def test_published_with_policy_incorrect(self, mylog):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=notexist'))
        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect
            self.assertRaises(
                oslo.messaging.MessagingDisconnected,
                publisher.publish_samples,
                mock.MagicMock(), self.test_data)
            self.assertTrue(mylog.warn.called)
            self.assertEqual(publisher.policy, 'default')
            self.assertEqual(len(publisher.local_queue), 0)
            prepare.assert_called_once_with(
                topic=self.CONF.publisher_rpc.metering_topic)

    def test_published_with_policy_drop_and_rpc_down(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=drop'))
        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect
            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)
            self.assertEqual(len(publisher.local_queue), 0)
            prepare.assert_called_once_with(
                topic=self.CONF.publisher_rpc.metering_topic)

    def test_published_with_policy_queue_and_rpc_down(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=queue'))
        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect

            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)
            self.assertEqual(len(publisher.local_queue), 1)
            prepare.assert_called_once_with(
                topic=self.CONF.publisher_rpc.metering_topic)

    def test_published_with_policy_queue_and_rpc_down_up(self):
        self.rpc_unreachable = True
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=queue'))

        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect
            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)

            self.assertEqual(len(publisher.local_queue), 1)

            prepare.side_effect = mock.MagicMock()
            publisher.publish_samples(mock.MagicMock(),
                                      self.test_data)

            self.assertEqual(len(publisher.local_queue), 0)

            topic = self.CONF.publisher_rpc.metering_topic
            expected = [mock.call(topic=topic),
                        mock.call(topic=topic),
                        mock.call(topic=topic)]
            self.assertEqual(prepare.mock_calls, expected)

    def test_published_with_policy_sized_queue_and_rpc_down(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=queue&max_queue_length=3'))

        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect
            for i in range(0, 5):
                for s in self.test_data:
                    s.source = 'test-%d' % i
                publisher.publish_samples(mock.MagicMock(),
                                          self.test_data)

        self.assertEqual(len(publisher.local_queue), 3)
        self.assertEqual(
            publisher.local_queue[0][2][0]['source'],
            'test-2'
        )
        self.assertEqual(
            publisher.local_queue[1][2][0]['source'],
            'test-3'
        )
        self.assertEqual(
            publisher.local_queue[2][2][0]['source'],
            'test-4'
        )

    def test_published_with_policy_default_sized_queue_and_rpc_down(self):
        publisher = rpc.RPCPublisher(
            network_utils.urlsplit('rpc://?policy=queue'))

        side_effect = oslo.messaging.MessagingDisconnected()
        with mock.patch.object(publisher.rpc_client, 'prepare') as prepare:
            prepare.side_effect = side_effect
            for i in range(0, 2000):
                for s in self.test_data:
                    s.source = 'test-%d' % i
                publisher.publish_samples(mock.MagicMock(),
                                          self.test_data)

        self.assertEqual(len(publisher.local_queue), 1024)
        self.assertEqual(
            publisher.local_queue[0][2][0]['source'],
            'test-976'
        )
        self.assertEqual(
            publisher.local_queue[1023][2][0]['source'],
            'test-1999'
        )
