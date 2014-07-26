import nose.tools as n

import at.updater as u

def test_purge_stale():
    timeout = 60
    active_devices = {
        'addr1': (1406362740.570188, '192.168.1.2', 'tom'),
        'addr2': (1006362740.0, '192.168.1.82', 'william'),
    }
    expected = {'addr1': active_devices['addr1']}
    observed = u.purge_stale(timeout, active_devices, now = 1406362750.570188)
    n.assert_dict_equal(observed, expected)

def test_get_device():
    active_devices = {
        'addr1': (1406362740.570188, '192.168.1.2', 'tom'),
        'addr2': (1006362740.0, '192.168.1.82', 'william'),
    }
    n.assert_tuple_equal(u.get_device(active_devices, '192.168.1.82'), ('addr2', 'william'))
    n.assert_tuple_equal(u.get_device(active_devices, '192.168.4.10'), (None, None))

