# -*- encoding: utf-8 -*-
#
# Copyright © 2012 New Dream Network, LLC (DreamHost)
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
"""Base class for plugins.
"""

import abc
import fnmatch

import six

from ceilometer import messaging
from ceilometer.openstack.common import context


class PluginBase(object):
    """Base class for all plugins.
    """


@six.add_metaclass(abc.ABCMeta)
class NotificationBase(PluginBase):
    """Base class for plugins that support the notification API."""
    def __init__(self, pipeline_manager):
        self.pipeline_manager = pipeline_manager

    @abc.abstractproperty
    def event_types(self):
        """Return a sequence of strings defining the event types to be
        given to this plugin.
        """

    @abc.abstractmethod
    def get_targets(self, conf):
        """Return a sequence of oslo.messaging.Target defining the exchange and
        topics to be connected for this plugin.

        :param conf: Configuration.
        """

    @abc.abstractmethod
    def process_notification(self, message):
        """Return a sequence of Counter instances for the given message.

        :param message: Message to process.
        """

    @staticmethod
    def _handle_event_type(event_type, event_type_to_handle):
        """Check whether event_type should be handled according to
        event_type_to_handle.

        """
        return any(map(lambda e: fnmatch.fnmatch(event_type, e),
                       event_type_to_handle))

    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        """RPC endpoint for notification messages

        When another service sends a notification over the message
        bus, this method receives it.

        """
        notification = messaging.convert_to_old_notification_format(
            'info', ctxt, publisher_id, event_type, payload, metadata)
        self.to_samples_and_publish(context.get_admin_context(), notification)

    def to_samples_and_publish(self, context, notification):
        """Return samples produced by *process_notification* for the given
        notification.

        TODO(sileht): this will be moved into oslo.messaging
        cf: the oslo.messaging bp notification-dispatcher-filter

        :param notification: The notification to process.

        """
        if not self._handle_event_type(notification['event_type'],
                                       self.event_types):
            return

        with self.pipeline_manager.publisher(context) as p:
            p(list(self.process_notification(notification)))


@six.add_metaclass(abc.ABCMeta)
class PollsterBase(PluginBase):
    """Base class for plugins that support the polling API."""

    @abc.abstractmethod
    def get_samples(self, manager, cache, resources=[]):
        """Return a sequence of Counter instances from polling the resources.

        :param manager: The service manager class invoking the plugin.
        :param cache: A dictionary to allow pollsters to pass data
                      between themselves when recomputing it would be
                      expensive (e.g., asking another service for a
                      list of objects).
        :param resources: A list of the endpoints the pollster will get data
                          from. It's up to the specific pollster to decide
                          how to use it.

        """


@six.add_metaclass(abc.ABCMeta)
class DiscoveryBase(object):
    @abc.abstractmethod
    def discover(self, param=None):
        """Discover resources to monitor.
        :param param: an optional parameter to guide the discovery
        """
