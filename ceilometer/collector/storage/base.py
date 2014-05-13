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

cfg.CONF.register_opts(STORAGE_OPTS, group="collector")


class Connection(object):
    """Base class for storage system connections."""

    """A dictionary representing the capabilities of this driver.
    """
    CAPABILITIES = {
        'meters': {'pagination': False,
                   'query': {'simple': False,
                             'metadata': False,
                             'complex': False}},
        'resources': {'pagination': False,
                      'query': {'simple': False,
                                'metadata': False,
                                'complex': False}},
        'samples': {'pagination': False,
                    'groupby': False,
                    'query': {'simple': False,
                              'metadata': False,
                              'complex': False}},
        'statistics': {'pagination': False,
                       'groupby': False,
                       'query': {'simple': False,
                                 'metadata': False,
                                 'complex': False},
                       'aggregation': {'standard': False,
                                       'selectable': {
                                           'max': False,
                                           'min': False,
                                           'sum': False,
                                           'avg': False,
                                           'count': False,
                                           'stddev': False,
                                           'cardinality': False}}
                       },
    }

    def __init__(self, url):
        """Constructor."""
        pass

    @staticmethod
    def upgrade():
        """Migrate the database to `version` or the most recent version."""

    @staticmethod
    def record_metering_data(data):
        """Write the data to the backend storage system.

        :param data: a dictionary such as returned by
                     ceilometer.meter.meter_message_from_counter

        All timestamps must be naive utc datetime object.
        """
        raise NotImplementedError('Projects not implemented')

    @staticmethod
    def clear_expired_metering_data(ttl):
        """Clear expired data from the backend storage system according to the
        time-to-live.

        :param ttl: Number of seconds to keep records for.

        """
        raise NotImplementedError('Clearing samples not implemented')

    @staticmethod
    def get_users(source=None):
        """Return an iterable of user id strings.

        :param source: Optional source filter.
        """
        raise NotImplementedError('Users not implemented')

    @staticmethod
    def get_projects(source=None):
        """Return an iterable of project id strings.

        :param source: Optional source filter.
        """
        raise NotImplementedError('Projects not implemented')

    @staticmethod
    def get_resources(user=None, project=None, source=None,
                      start_timestamp=None, start_timestamp_op=None,
                      end_timestamp=None, end_timestamp_op=None,
                      metaquery={}, resource=None, pagination=None):
        """Return an iterable of models.Resource instances containing
        resource information.

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param source: Optional source filter.
        :param start_timestamp: Optional modified timestamp start range.
        :param start_timestamp_op: Optional timestamp start range operation.
        :param end_timestamp: Optional modified timestamp end range.
        :param end_timestamp_op: Optional timestamp end range operation.
        :param metaquery: Optional dict with metadata to match on.
        :param resource: Optional resource filter.
        :param pagination: Optional pagination query.
        """
        raise NotImplementedError('Resources not implemented')

    @staticmethod
    def get_meters(user=None, project=None, resource=None, source=None,
                   metaquery={}, pagination=None):
        """Return an iterable of model.Meter instances containing meter
        information.

        :param user: Optional ID for user that owns the resource.
        :param project: Optional ID for project that owns the resource.
        :param resource: Optional resource filter.
        :param source: Optional source filter.
        :param metaquery: Optional dict with metadata to match on.
        :param pagination: Optional pagination query.
        """
        raise NotImplementedError('Meters not implemented')

    @staticmethod
    def get_samples(sample_filter, limit=None):
        """Return an iterable of model.Sample instances.

        :param sample_filter: Filter.
        :param limit: Maximum number of results to return.
        """
        raise NotImplementedError('Samples not implemented')

    @staticmethod
    def get_meter_statistics(sample_filter, period=None, groupby=None,
                             aggregate=None):
        """Return an iterable of model.Statistics instances.

        The filter must have a meter value set.
        """
        raise NotImplementedError('Statistics not implemented')

    @staticmethod
    def clear():
        """Clear database."""

    @staticmethod
    def query_samples(filter_expr=None, orderby=None, limit=None):
        """Return an iterable of model.Sample objects.

        :param filter_expr: Filter expression for query.
        :param orderby: List of field name and direction pairs for order by.
        :param limit: Maximum number of results to return.
        """

        raise NotImplementedError('Complex query for samples '
                                  'is not implemented.')

    @classmethod
    def get_capabilities(cls):
        """Return an dictionary representing the capabilities of each driver.
        """
        return cls.CAPABILITIES
