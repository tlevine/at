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

def update(lease_offset, active_devices, hwaddr, atime = None, ip = None, name = None):
    _active_devices = dict(active_devices)
    if atime:
        atime -= lease_offset
    else:
        atime = time() 
    _active_devices[hwaddr] = (atime, ip, name)
    logger.info('updated %s with atime %s and ip %s',
        hwaddr, util.strfts(atime), ip)
    return _active_devices


def watch(lease_file, last_modified = 0, active_devices = {}):
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
                        update(active_devices, hwaddr, atime, ip, name)
            last_modified = mtime
            sleep(3.0)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error('Updater got an exception:\n' + \
                traceback.format_exc(e))
            sleep(10.0)
