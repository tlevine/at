import os
import traceback
import threading
from time import sleep, time
from logging import getLogger

import util
import parse

logger = getLogger('at')

def purge_stale(timeout, active_devices):
    active = dict(active_devices)
    now = time()
    for addr, (atime, ip, name) in active.items():
        if now - atime > timeout:
            del active[addr]

def get_device(active_devices, ip):
    for hwaddr, (atime, dip, name) in \
        active_devices.iteritems():
        if ip == dip:
            return hwaddr, name
    return None, None

def update(lease_offset, timeout, active_devices, hwaddr, atime = None, ip = None, name = None):
    _active_devices = purge_stale(timeout, active_devices)
    if atime:
        atime -= lease_offset
    else:
        atime = time() 
    _active_devices[hwaddr] = (atime, ip, name)
    logger.info('updated %s with atime %s and ip %s',
        hwaddr, util.strfts(atime), ip)
    return _active_devices

def watch(active_devices, lease_offset, timeout, lease_file, last_modified = 0):
    '''
    active_devices :: multiprocessing.Manager.dict
    '''
    _update = partial(update, lease_offset, timeout)
    while True:
        if not os.path.isfile(lease_file):
            logger.error('Lease file %s does not exist.' % lease_file)
            break
        try:
            mtime = os.stat(lease_file).st_mtime
            if mtime > last_modified:
                logger.info('Lease file changed, updating')
                with open(lease_file, 'r') as f:
                    for hwaddr, atime, ip, name in parse.lease_file(f):
                        active_devices = _update(active_devices, hwaddr, atime, ip, name)
            last_modified = mtime
            sleep(3.0)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error('Updater got an exception:\n' + \
                traceback.format_exc(e))
            sleep(10.0)

active_devices = Manager().dict()
Process(target = watch, args = (active_devices, lease_offset, timeout, lease_file)

def now_at(active_devices, db):
    'dict[devices] -> dict[users, unknown]'
    device_infos = list(queries.get_device_infos(db, active_devices.keys()))
    device_infos.sort(key=lambda di: active_devices.__getitem__)
    users = list(dict((info.owner, active_devices[info.hwaddr][0]) for info in device_infos 
        if info.owner and not info.ignored).iteritems())
    users.sort(key=lambda (u, a): a, reverse=True)
    unknown = set(active_devices.keys()) - set(d.hwaddr for d in device_infos)
    return dict(users=users, unknown=unknown)
