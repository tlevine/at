import nose.tools as n

import at.queries as q
import at.updater as u

def test_purge_stale():
    timeout = 60
    active_devices = {
        u'addr1': (1406362740.570188, u'192.168.1.2', u'tom'),
        u'addr2': (1006362740.0, u'192.168.1.82', u'william'),
    }
    expected = {'addr1': active_devices['addr1']}
    observed = u.purge_stale(timeout, active_devices, now = 1406362750.570188)
    n.assert_dict_equal(observed, expected)

def test_get_device():
    active_devices = {
        u'addr1': (1406362740.570188, u'192.168.1.2', u'tom'),
        u'addr2': (1006362740.0, u'192.168.1.82', u'william'),
    }
    n.assert_tuple_equal(u.get_device(active_devices, u'192.168.1.82'), ('addr2', u'william'))
    n.assert_tuple_equal(u.get_device(active_devices, u'192.168.4.10'), (None, None))

def test_update():
    lease_offset = 240
    active_devices = {
        u'addr1': (1406362740.570188, u'192.168.1.2', u'tom'),
        u'addr2': (1006362740.0, u'192.168.1.82', u'william'),
    }
    hwaddr = u'addr1'
    atime = 1406362780.0
    ip = u'192.168.1.117'
    name = u'zamenhof'

    expected = {
        u'addr1': (atime - lease_offset, ip, name),
        u'addr2': active_devices['addr2'],
    }

    observed = u.update(lease_offset, active_devices, hwaddr, atime, ip, name)
    n.assert_dict_equal(observed, expected)

def test_now_at():
    active_devices = {
        u'claimed-hwaddr': (1406362740.570188, u'192.168.1.2', u'wildebeest'),
        u'unclaimed-hwaddr': (1006362740.0, u'192.168.1.82', u'occurrence'),
    }
    tlevine = q.User(3, 'tlevine', 'blah blah blah', 'http://dada.pink')
    expected = [
        (u'tlevine', u'claimed-hwaddr', u'192.168.1.2', active_devices[u'claimed-hwaddr'][0]),
        (None, u'unclaimed-hwaddr', u'192.168.1.82', active_devices[u'unclaimed-hwaddr'][0]),
    ]
    def fake_get_device_infos(db, hwaddrs):
        for hwaddr in hwaddrs:
            owner = u'tlevine' if hwaddr == u'claimed-hwaddr' else None
            yield q.DeviceInfo(hwaddr, active_devices[hwaddr][2], owner, 0)

    observed = list(u.now_at(active_devices, None, get_device_infos = fake_get_device_infos))
    n.assert_list_equal(observed, expected)
