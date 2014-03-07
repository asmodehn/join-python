#!/usr/bin/python3
# -*- python -*-
'''
join python – Join-calculus for Python
Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import time

import random
import threading


class signal:
    def __init__(self, f):
        self.f = f
    
    def __call__(self, *args, **kwargs):
        class signal_:
            def __init__(self, f):
                def f_():
                    self.rc = f(*args, **kwargs)
                self.rc = None
                self.t = threading.Thread(target = f_)
                self.t.start()
            def join(self):
                self.t.join()
                return self.rc
        return signal_(self.f)


class fragment:
    def __init__(self, f):
        self.f = f
        self.queue = []
        self.condition = threading.Condition()
    
    def __call__(self, *args, **kwargs):
        self.f(*args, **kwargs)
        self.condition.acquire()
        self.queue.append((args, kwargs))
        self.condition.notify()
        self.condition.release()
    
    def unjoin(self, args, kwargs):
        self.condition.acquire()
        self.queue.insert(0, (args, kwargs))
        self.condition.notify()
        self.condition.release()


def join(*fs):
    rc = []
    for f in fs:
        f.condition.acquire()
        f.condition.wait()
        rc.append(f.queue.pop(0))
        f.condition.release()
    return rc[0] if len(fs) == 1 else rc


def ordered_join(*f_groups):
    condition = threading.Condition()
    rc = None
    index = 0
    for f_group in f_groups:
        def join_(fs, index):
            params = join(*fs)
            already_done = rc is not None
            if not already_done:
                condition.acquire()
            if rc is None:
                params = (index, rc)
                condition.notify()
                condition.release()
            else:
                if not already_done:
                    condition.release()
                if len(fs) == 1:
                    fs[0].unjoin(*params)
                else:
                    for i, f in enumerate(fs):
                        f.unjoin(*(params[i]))
        threading.Thread(target = join_, args = (f_group, index)).start()
        index += 1
    condition.acquire()
    condition.wait()
    condition.release()
    return rc


def unordered_join(*f_groups):
    ready = [i for i, fs in enumerate(f_groups) if all([len(f.queue) for f in fs])]
    if len(ready):
        i = ready[random.randrange(len(ready))]
        return (i, join(*(f_groups[i])))
    else:
        return ordered_join(*f_groups)


def concurrently(*fs):
    ts = [threading.Thread(target = f, args = args, kwargs = kwargs) for f in fs]
    for t in ts:
        ts.start()
    for t in ts:
        ts.join()


class test:
    @signal
    def signal(f, *args):
        f(*args)
        return 'test'
    
    @fragment
    def fragment(*args, **kwargs):
        pass
    
    def join(param):
        (jargs, jkwargs) = join(test.fragment)
        print(param, dict(jkwargs), *jargs)


s = test.signal(test.join, 'join')
time.sleep(1)
test.fragment('arg1', 'arg2', a = 'A', b = 'B')
print(s.join())

