import os
import json

import nose.tools as n

import at.parse as parse

def test_lease_file():
    with open(os.path.join('at','test','fixtures','leases')) as fp:
        observed = list(parse.lease_file(fp))
    from at.test.fixtures.leases import leases as expected
    n.assert_list_equal(observed, expected)
