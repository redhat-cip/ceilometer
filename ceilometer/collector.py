# -*- encoding: utf-8 -*-
#
# Copyright © 2012-2013 eNovance <licensing@enovance.com>
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

import asyncio
import socket

import msgpack
from oslo.config import cfg
import oslo.messaging

from ceilometer import messaging
from ceilometer.openstack.common.gettextutils import _  # noqa
from ceilometer.openstack.common import log
from ceilometer import service

OPTS = [
    cfg.StrOpt('udp_address',
               default='0.0.0.0',
               help='Address to which the UDP socket is bound. Set to '
               'an empty string to disable.'),
    cfg.IntOpt('udp_port',
               default=4952,
               help='Port to which the UDP socket is bound.'),
]

cfg.CONF.register_opts(OPTS, group="collector")
cfg.CONF.import_opt('metering_topic', 'ceilometer.publisher.messaging',
                    group="publisher_rpc")
cfg.CONF.import_opt('metering_topic', 'ceilometer.publisher.messaging',
                    group="publisher_notifier")


LOG = log.getLogger(__name__)


class CollectorService(service.DispatchedService, service.Service,
                       asyncio.DatagramProtocol):
    """Listener for the collector service."""

    def __init__(self):
        super(CollectorService, self).__init__()
        if self.messaging_enabled():
            # FIXME(sileht): oslo.messaging force us to have the same
            # queue and topic name, Should we add ceilometer.collector
            # to the topic ?
            self.rpc_server = messaging.get_rpc_server(
                cfg.CONF.publisher_rpc.metering_topic, self)
            target = oslo.messaging.Target(
                topic=cfg.CONF.publisher_notifier.metering_topic)
            self.notification_server = messaging.get_notification_listener(
                [target], [self])

    @staticmethod
    def messaging_enabled():
        # cfg.CONF opt from oslo.messaging.transport
        return cfg.CONF.rpc_backend or cfg.CONF.transport_url

    def start(self):
        """Bind the UDP socket and handle incoming data."""
        super(CollectorService, self).start()
        if cfg.CONF.collector.udp_address:
            self.start_udp()

        if self.messaging_enabled():
            self.rpc_server.start()
            self.notification_server.start()

    def wait(self):
        """Bind the UDP socket and handle incoming data."""
        super(CollectorService, self).wait()
        if self.rpc_enabled():
            self.rpc_server.wait()

    def start_udp(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.bind((cfg.CONF.collector.udp_address,
                  cfg.CONF.collector.udp_port))
        loop = asyncio.get_event_loop()
        task = asyncio.Task(loop.create_connection(lambda: self, sock=udp))
        self.tg.add_task(task)

    def stop(self):
        self.udp_run = False
        if self.messaging_enabled():
            self.rpc_server.stop()
            self.notification_server.stop()
        super(CollectorService, self).stop()

    def sample(self, ctxt, publisher_id, event_type, payload, metadata):
        """RPC endpoint for notification messages

        When another service sends a notification over the message
        bus, this method receives it.

        """
        self.dispatcher_manager.map_method('record_metering_data',
                                           data=payload)

    def record_metering_data(self, context, data):
        """RPC endpoint for messages we send to ourselves.

        When the notification messages are re-published through the
        RPC publisher, this method receives them for processing.
        """
        self.dispatcher_manager.map_method('record_metering_data', data=data)

    def data_received(self, data):
        # NOTE(sileht): trollius use data_received instead of
        # datagram_received ?
        self.datagram_received(data, source=None)

    def datagram_received(self, data, source):
        try:
            sample = msgpack.loads(data)
        except Exception:
            LOG.warn(_("UDP: Cannot decode data sent by %s"), str(source))
        else:
            try:
                LOG.debug(_("UDP: Storing %s"), str(sample))
                self.dispatcher_manager.map_method('record_metering_data',
                                                   sample)
            except Exception:
                LOG.exception(_("UDP: Unable to store meter"))

    def error_received(self, exc):
        LOG.error('UDP collector error: %s' % exc)
