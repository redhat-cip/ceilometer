# Copyright 2012 Red Hat, Inc.
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

from ceilometer.openstack.common import log as logging
from ceilometer.openstack.common import loopingcall


LOG = logging.getLogger(__name__)


class ThreadGroup(object):
    """The point of the ThreadGroup class is to:

    * keep track of asyncio tasks (making it easier to stop them when need be).
    * provide an easy API to add timers.
    """
    def __init__(self):
        self.pending_tasks = []

    def add_dynamic_timer(self, callback, initial_delay=None,
                          periodic_interval_max=None, *args, **kwargs):
        timer = loopingcall.DynamicLoopingCall(callback, *args, **kwargs)
        task = timer.start(initial_delay=initial_delay,
                           periodic_interval_max=periodic_interval_max)
        self.add_task(task)

    def add_timer(self, interval, callback, initial_delay=None,
                  *args, **kwargs):
        pulse = loopingcall.FixedIntervalLoopingCall(callback, *args, **kwargs)
        task = pulse.start(interval=interval, initial_delay=initial_delay)
        self.add_task(task)

    def add_task(self, task):
        def callback_done(f):
            self.pending_tasks.remove(task)

        task.add_done_callback(callback_done)
        self.pending_tasks.append(task)

    def add_thread(self, callback, *args, **kwargs):
        """Deprecated: just for compat"""

        @asyncio.coroutine
        def callback_wrapper(callback, *args, **kwargs):
            callback(*args, **kwargs)

        task = asyncio.Task(callback_wrapper(callback, *args, **kwargs))
        self.add_task(task)

    def stop(self):
        for x in self.pending_tasks[:]:
            x.cancel()

    def wait(self):
        yield asyncio.wait(self.pending_tasks)
        self.pending_tasks = []
