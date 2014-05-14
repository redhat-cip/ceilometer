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

import six

from ceilometer.openstack.common import timeutils
from ceilometer import utils
from ceilometer.storage import base


class Event(base.Model):
    """A raw event from the source system. Events have Traits.

       Metrics will be derived from one or more Events.
    """

    DUPLICATE = 1
    UNKNOWN_PROBLEM = 2

    def __init__(self, message_id, event_type, generated, traits):
        """Create a new event.

        :param message_id:  Unique ID for the message this event
                            stemmed from. This is different than
                            the Event ID, which comes from the
                            underlying storage system.
        :param event_type:  The type of the event.
        :param generated:   UTC time for when the event occurred.
        :param traits:      list of Traits on this Event.
        """
        base.Model.__init__(self, message_id=message_id, event_type=event_type,
                            generated=generated, traits=traits)

    def append_trait(self, trait_model):
        self.traits.append(trait_model)

    def __repr__(self):
        trait_list = []
        if self.traits:
            trait_list = [str(trait) for trait in self.traits]
        return "<Event: %s, %s, %s, %s>" % \
            (self.message_id, self.event_type, self.generated,
             " ".join(trait_list))


class Trait(base.Model):
    """A Trait is a key/value pair of data on an Event. The value is variant
    record of basic data types (int, date, float, etc).
    """

    NONE_TYPE = 0
    TEXT_TYPE = 1
    INT_TYPE = 2
    FLOAT_TYPE = 3
    DATETIME_TYPE = 4

    type_names = {
        NONE_TYPE: "none",
        TEXT_TYPE: "string",
        INT_TYPE: "integer",
        FLOAT_TYPE: "float",
        DATETIME_TYPE: "datetime"
    }

    def __init__(self, name, dtype, value):
        if not dtype:
            dtype = Trait.NONE_TYPE
        base.Model.__init__(self, name=name, dtype=dtype, value=value)

    def __repr__(self):
        return "<Trait: %s %d %s>" % (self.name, self.dtype, self.value)

    def get_type_name(self):
        return self.get_name_by_type(self.dtype)

    @classmethod
    def get_type_by_name(cls, type_name):
        return getattr(cls, '%s_TYPE' % type_name.upper(), None)

    @classmethod
    def get_type_names(cls):
        return cls.type_names.values()

    @classmethod
    def get_name_by_type(cls, type_id):
        return cls.type_names.get(type_id, "none")

    @classmethod
    def convert_value(cls, trait_type, value):
        if trait_type is cls.INT_TYPE:
            return int(value)
        if trait_type is cls.FLOAT_TYPE:
            return float(value)
        if trait_type is cls.DATETIME_TYPE:
            return timeutils.normalize_time(timeutils.parse_isotime(value))
        return str(value)


class EventFilter(object):
    """Properties for building an Event query.

    :param start_time: UTC start datetime (mandatory)
    :param end_time: UTC end datetime (mandatory)
    :param event_type: the name of the event. None for all.
    :param message_id: the message_id of the event. None for all.
    :param traits_filter: the trait filter dicts, all of which are optional.
                   This parameter is a list of dictionaries that specify
                   trait values:
                    {'key': <key>,
                    'string': <value>,
                    'integer': <value>,
                    'datetime': <value>,
                    'float': <value>,
                    'op': <eq, lt, le, ne, gt or ge> }
    """

    def __init__(self, start_time=None, end_time=None, event_type=None,
                 message_id=None, traits_filter=[]):
        self.start_time = utils.sanitize_timestamp(start_time)
        self.end_time = utils.sanitize_timestamp(end_time)
        self.message_id = message_id
        self.event_type = event_type
        self.traits_filter = traits_filter

    def __repr__(self):
        return ("<EventFilter(start_time: %s,"
                " end_time: %s,"
                " event_type: %s,"
                " traits: %s)>" %
                (self.start_time,
                 self.end_time,
                 self.event_type,
                 six.text_type(self.traits_filter)))
