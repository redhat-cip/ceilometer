# -*- encoding: utf-8 -*-
#
# Copyright © 2014 eNovance <licensing@enovance.com>
#
# Authors: Mehdi Abaakouk <mehdi.abaakouk@enovance.com>
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

from oslo.config import cfg

STORAGE_OPTS = [
    cfg.StrOpt('database_connection', default=None,),
]

cfg.CONF.register_opts(STORAGE_OPTS, group="event")


class Connection(object):
    """Base class for storage system connections."""

    """A dictionary representing the capabilities of this driver.
    """
    CAPABILITIES = {
        'events': {'query': {'simple': False}},
    }

    def __init__(self, url):
        """Constructor."""
        pass

    @staticmethod
    def upgrade():
        """Migrate the database to `version` or the most recent version."""

        """Clear expired data from the backend storage system according to the
        time-to-live.

        :param ttl: Number of seconds to keep records for.

        """
        raise NotImplementedError('Clearing samples not implemented')

    @staticmethod
    def clear():
        """Clear database."""

    @staticmethod
    def record_events(events):
        """Write the events to the backend storage system.

        :param events: a list of model.Event objects.
        """
        raise NotImplementedError('Events not implemented.')

    @staticmethod
    def get_events(event_filter):
        """Return an iterable of model.Event objects.
        """
        raise NotImplementedError('Events not implemented.')

    @staticmethod
    def get_event_types():
        """Return all event types as an iterable of strings.
        """
        raise NotImplementedError('Events not implemented.')

    @staticmethod
    def get_trait_types(event_type):
        """Return a dictionary containing the name and data type of
        the trait type. Only trait types for the provided event_type are
        returned.

        :param event_type: the type of the Event
        """
        raise NotImplementedError('Events not implemented.')

    @staticmethod
    def get_traits(event_type, trait_type=None):
        """Return all trait instances associated with an event_type. If
        trait_type is specified, only return instances of that trait type.

        :param event_type: the type of the Event to filter by
        :param trait_type: the name of the Trait to filter by
        """

        raise NotImplementedError('Events not implemented.')

    @classmethod
    def get_capabilities(cls):
        """Return an dictionary representing the capabilities of each driver.
        """
        return cls.CAPABILITIES
