import os
import traceback
from time import sleep, time
from logging import getLogger
from functools import partial

import util
import parse
import queries

logger = getLogger('at')

def purge_stale(timeout, active_devices, now = time()):
    active = dict(active_devices)
    for addr, (atime, ip, name) in active.items():
        if now - atime > timeout:
            del active[addr]
    return active

def get_device(active_devices, ip):
    for hwaddr, (atime, dip, name) in \
        active_devices.items():
        if ip == dip:
            return hwaddr, name
    return None, None

def update(lease_offset, active_devices, hwaddr, atime, ip, name):
    _active_devices = dict(active_devices)
    atime = int(atime) - lease_offset
    _active_devices[hwaddr] = (atime, ip, name)
    logger.info('updated %s with atime %s and ip %s',
        hwaddr, util.strfts(atime), ip)
    return _active_devices

def watch(active_devices, lease_offset, timeout, lease_file, last_modified = 0):
    '''
    active_devices :: multiprocessing.Manager.dict
    '''
    _update = partial(update, lease_offset)
    while True:
        if not os.path.isfile(lease_file):
            logger.error('Lease file %s does not exist.' % lease_file)
            break
        try:
            mtime = os.stat(lease_file).st_mtime
            if mtime > last_modified:
                logger.info('Lease file changed, updating')
                with open(lease_file, 'r') as f:
                    active_devices = purge_stale(timeout, active_devices)
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

def now_at(active_devices, db, get_device_infos = queries.get_device_infos):
    'dict[devices] -> dict[users, unknown]'
    for device_info in get_device_infos(db, active_devices.keys()):
        yield (
            device_info.owner, device_info.hwaddr,
            active_devices[device_info.hwaddr][1],
            active_devices[device_info.hwaddr][0]
        )
