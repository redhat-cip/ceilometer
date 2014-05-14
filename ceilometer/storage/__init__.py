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
"""Storage backend management
"""

import six.moves.urllib.parse as urlparse

from oslo.config import cfg
from stevedore import driver

from ceilometer.openstack.common.gettextutils import _
from ceilometer.openstack.common import log


LOG = log.getLogger(__name__)

OLD_STORAGE_OPTS = [
    cfg.StrOpt('database_connection',
               secret=True,
               default=None,
               help='DEPRECATED - Database connection string.',
               ),
]

cfg.CONF.register_opts(OLD_STORAGE_OPTS)


STORAGE_OPTS = [
    cfg.IntOpt('time_to_live',
               default=-1,
               help="Number of seconds that samples are kept "
               "in the database for (<= 0 means forever)."),
]

cfg.CONF.register_opts(STORAGE_OPTS, group='database')

cfg.CONF.import_opt('connection',
                    'ceilometer.openstack.common.db.options',
                    group='database')

cfg.CONF.import_opt('database_connection', 'ceilometer.alarm.storage.base',
                    group='alarm')
cfg.CONF.import_opt('database_connection', 'ceilometer.collector.storage.base',
                    group='collector')
cfg.CONF.import_opt('database_connection', 'ceilometer.event.storage.base',
                    group='event')


class StorageBadVersion(Exception):
    """Error raised when the storage backend version is not good enough."""


class StorageBadAggregate(Exception):
    """Error raised when an aggregate is unacceptable to storage backend."""
    code = 400


def get_connections_from_config(conf):
    conns = {}
    for group in ['alarm', 'event', 'collector']:
        conns[group] = get_connection_from_config(conf, group)
    return conns


def get_connection_from_config(conf, group):
    if conf.database_connection:
        conf.set_override('connection', conf.database_connection,
                          group='database')

    cfg_group = getattr(conf, group, None)
    if cfg_group and cfg_group.database_connection:
        url = cfg_group.database_connection
    else:
        url = conf.database.connection
    return get_connection(url, "ceilometer.%s.storage" % group)


def get_connection(url, namespace):
    """Return an open connection to the database."""
    engine_name = urlparse.urlparse(url).scheme
    LOG.debug(_('looking for %(name)r driver in %(namespace)r') % (
              {'name': engine_name,
               'namespace': namespace}))
    mgr = driver.DriverManager(namespace, engine_name)
    return mgr.driver(url)
