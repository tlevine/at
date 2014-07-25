import traceback
import threading
from time import sleep, time

import parse

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
        app.logger.info('updated %s with atime %s and ip %s',
            hwaddr, strfts(atime), ip)

class CapUpdater(Updater):
    def __init__(self, cap_file, *a, **kw):
        self.cap_file = cap_file
        Updater.__init__(self, *a, **kw)
    def run(self):
        while True:
            if not os.path.isfile(self.cap_file):
                app.logger.error('Cap file %s does not exist.' % self.cap_file)
                break
            try:
                with open(self.cap_file, 'r', buffering=0) as f:
                    app.logger.info('Updater ready on cap file %s', self.cap_file)
                    while True:
                        hwaddr = f.readline().strip()
                        if not hwaddr:
                            break
                        self.update(hwaddr)
                app.logger.warning('Cap file %s closed, reopening', self.cap_file)
            except Exception as e:
                app.logger.error('Updater got an exception:\n' + \
                    traceback.format_exc(e))
                sleep(10.0)

class MtimeUpdater(Updater):
    def __init__(self, lease_file, *a, **kw):
        self.lease_file = lease_file
        self.last_modified = 0
        Updater.__init__(self, *a, **kw)
    def file_changed(self, f):
        pass
    def run(self):
        import os
        while True:
            if not os.path.isfile(self.lease_file):
                app.logger.error('Lease file %s does not exist.' % self.lease_file)
                break
            try:
                mtime = os.stat(self.lease_file).st_mtime
                if mtime > self.last_modified:
                    app.logger.info('Lease file changed, updating')
                    with open(self.lease_file, 'r') as f:
                        self.file_changed(f)
                self.last_modified = mtime
                sleep(3.0)
            except Exception as e:
                app.logger.error('Updater got an exception:\n' + \
                    traceback.format_exc(e))
                sleep(10.0)

class DhcpdUpdater(MtimeUpdater):
    def file_changed(self, f):
        for hwaddr, atime, ip, name in parse.lease_file(f):
            self.update(hwaddr, atime, ip, name)

def now_at():
    devices = updater.get_active_devices()
    device_infos = list(get_device_infos(g.db, devices.keys()))
    device_infos.sort(key=lambda di: devices.__getitem__)
    users = list(dict((info.owner, devices[info.hwaddr][0]) for info in device_infos 
        if info.owner and not info.ignored).iteritems())
    users.sort(key=lambda (u, a): a, reverse=True)
    unknown = set(devices.keys()) - set(d.hwaddr for d in device_infos)
    return dict(users=users, unknown=unknown)

