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
"""Base classes for storage engines
"""

import datetime
import inspect
import math

from six import moves

from ceilometer.alarm.storage import base as alarm_storage
from ceilometer.collector.storage import base as collector_storage
from ceilometer.event.storage import base as event_storage
from ceilometer.openstack.common import timeutils


def iter_period(start, end, period):
    """Split a time from start to end in periods of a number of seconds. This
    function yield the (start, end) time for each period composing the time
    passed as argument.

    :param start: When the period set start.
    :param end: When the period end starts.
    :param period: The duration of the period.

    """
    period_start = start
    increment = datetime.timedelta(seconds=period)
    for i in moves.xrange(int(math.ceil(
            timeutils.delta_seconds(start, end)
            / float(period)))):
        next_start = period_start + increment
        yield (period_start, next_start)
        period_start = next_start


def _handle_sort_key(model_name, sort_key=None):
    """Generate sort keys according to the passed in sort key from user.

    :param model_name: Database model name be query.(alarm, meter, etc.)
    :param sort_key: sort key passed from user.
    return: sort keys list
    """
    sort_keys_extra = {'alarm': ['name', 'user_id', 'project_id'],
                       'meter': ['user_id', 'project_id'],
                       'resource': ['user_id', 'project_id', 'timestamp'],
                       }

    sort_keys = sort_keys_extra[model_name]
    if not sort_key:
        return sort_keys
    # NOTE(Fengqian): We need to put the sort key from user
    # in the first place of sort keys list.
    try:
        sort_keys.remove(sort_key)
    except ValueError:
        pass
    finally:
        sort_keys.insert(0, sort_key)
    return sort_keys


class MultipleResultsFound(Exception):
    pass


class NoResultFound(Exception):
    pass


class Pagination(object):
    """Class for pagination query."""

    def __init__(self, limit=None, primary_sort_dir='desc', sort_keys=[],
                 sort_dirs=[], marker_value=None):
        """This puts all parameters used for paginate query together.

        :param limit: Maximum number of items to return;
        :param primary_sort_dir: Sort direction of primary key.
        :param marker_value: Value of primary key to identify the last item of
                             the previous page.
        :param sort_keys: Array of attributes passed in by users to sort the
                            results besides the primary key.
        :param sort_dirs: Per-column array of sort_dirs, corresponding to
                            sort_keys.
        """
        self.limit = limit
        self.primary_sort_dir = primary_sort_dir
        self.marker_value = marker_value
        self.sort_keys = sort_keys
        self.sort_dirs = sort_dirs


class Model(object):
    """Base class for storage API models.
    """

    def __init__(self, **kwds):
        self.fields = list(kwds)
        for k, v in kwds.iteritems():
            setattr(self, k, v)

    def as_dict(self):
        d = {}
        for f in self.fields:
            v = getattr(self, f)
            if isinstance(v, Model):
                v = v.as_dict()
            elif isinstance(v, list) and v and isinstance(v[0], Model):
                v = [sub.as_dict() for sub in v]
            d[f] = v
        return d

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    @classmethod
    def get_field_names(cls):
        fields = inspect.getargspec(cls.__init__)[0]
        return set(fields) - set(["self"])


def get_merged_capabilities():
    capabilities = {}
    capabilities.update(alarm_storage.Connection.CAPABILITIES)
    capabilities.update(event_storage.Connection.CAPABILITIES)
    capabilities.update(collector_storage.Connection.CAPABILITIES)
    return capabilities
