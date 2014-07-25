import os
import traceback
import threading
from time import sleep, time
from logging import getLogger

import util
import parse

logger = getLogger('at')

class Updater(threading.Thread):
    def __init__(self,  timeout, lease_offset = 0, *a, **kw):
        self.timeout = timeout
        self.lock = threading.Lock()
        self.lease_offset = lease_offset
        self.active = {}
        threading.Thread.__init__(self, *a, **kw)
    def purge_stale(self):
        now = time()
        for addr, (atime, ip, name) in self.active.items():
            if now - atime > self.timeout:
                del self.active[addr]
    def get_active_devices(self):
        self.lock.acquire()
        self.purge_stale()
        r = dict(self.active)
        self.lock.release()
        return r
    def get_device(self, ip):
        for hwaddr, (atime, dip, name) in \
            self.get_active_devices().iteritems():
            if ip == dip:
                return hwaddr, name
        return None, None
    def update(self, hwaddr, atime = None, ip = None, name = None):
        if atime:
            atime -= self.lease_offset
        else:
            atime = time() 
        self.lock.acquire()
        self.active[hwaddr] = (atime, ip, name)
        self.lock.release()
        logger.info('updated %s with atime %s and ip %s',
            hwaddr, util.strfts(atime), ip)

class MtimeUpdater(Updater):
    def __init__(self, lease_file, *a, **kw):
        self.lease_file = lease_file
        self.last_modified = 0
        Updater.__init__(self, *a, **kw)
    def file_changed(self, f):
        pass
    def run(self):
        while True:
            if not os.path.isfile(self.lease_file):
                logger.error('Lease file %s does not exist.' % self.lease_file)
                break
            try:
                mtime = os.stat(self.lease_file).st_mtime
                if mtime > self.last_modified:
                    logger.info('Lease file changed, updating')
                    with open(self.lease_file, 'r') as f:
                        self.file_changed(f)
                self.last_modified = mtime
                sleep(3.0)
            except Exception as e:
                logger.error('Updater got an exception:\n' + \
                    traceback.format_exc(e))
                sleep(10.0)

class DhcpdUpdater(MtimeUpdater):
    def file_changed(self, f):
        for hwaddr, atime, ip, name in parse.lease_file(f):
            self.update(hwaddr, atime, ip, name)
