# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import asyncio

from ceilometer.openstack.common.gettextutils import _
from ceilometer.openstack.common import log as logging
from ceilometer.openstack.common import timeutils

LOG = logging.getLogger(__name__)


class LoopingCallDone(Exception):
    """Exception to break out and stop a LoopingCall.

    The poll-function passed to LoopingCall can raise this exception to
    break out of the loop normally. This is somewhat analogous to
    StopIteration.

    An optional return-value can be included as the argument to the exception;
    this return-value will be returned by LoopingCall.wait()

    """

    def __init__(self, retvalue=True):
        """:param retvalue: Value that LoopingCall.wait() should return."""
        self.retvalue = retvalue


class LoopingCallBase(object):
    def __init__(self, f=None, *args, **kw):
        self.args = args
        self.kw = kw
        self.f = f
        self.task = None

    def stop(self):
        if self.task:
            self.task.cancel()

    def wait(self):
        if self.task:
            yield asyncio.wait_for(self.task)


class FixedIntervalLoopingCall(LoopingCallBase):
    """A fixed interval looping call."""

    def start(self, interval, initial_delay=None):
        self.task = asyncio.Task(self.coroutine(interval=interval,
                                                initial_delay=initial_delay))
        return self.task

    @asyncio.coroutine
    def coroutine(self, interval, initial_delay=None):
        if initial_delay:
            yield asyncio.sleep(initial_delay)
        LOG.info('start loop')
        try:
            while True:
                start = timeutils.utcnow()
                self.f(*self.args, **self.kw)
                end = timeutils.utcnow()
                delay = interval - timeutils.delta_seconds(start, end)
                if delay <= 0:
                    LOG.warn(_('task run outlasted interval by %s sec') %
                             -delay)
                yield asyncio.sleep(delay if delay > 0 else 0)
        except LoopingCallDone:
            pass


# TODO(mikal): this class name is deprecated in Havana and should be removed
# in the I release
LoopingCall = FixedIntervalLoopingCall


class DynamicLoopingCall(LoopingCallBase):
    """A looping call which sleeps until the next known asyncio.

    The function called should return how long to sleep for before being
    called again.
    """

    def start(self, initial_delay=None, periodic_interval_max=None):
        return asyncio.Task(self.coroutine(
            initial_delay=initial_delay,
            periodic_interval_max=periodic_interval_max))

    @asyncio.coroutine
    def coroutine(self, initial_delay=None, periodic_interval_max=None):
        if initial_delay:
            yield asyncio.sleep(initial_delay)

        try:
            while True:
                idle = self.f(*self.args, **self.kw)
                if periodic_interval_max is not None:
                    idle = min(idle, periodic_interval_max)
                LOG.debug(_('Dynamic looping call sleeping for %.02f '
                            'seconds'), idle)
                yield asyncio.sleep(idle)
        except LoopingCallDone:
            pass
