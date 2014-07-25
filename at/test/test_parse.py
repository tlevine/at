import os
import json

import nose.tools as n

import at.parse as parse

def test_lease_file():
    with open(os.path.join('at','test','fixtures','lease-file')) as fp:
        observed = list(parse.lease_file(fp))
    with open(os.path.join('at','test','fixtures','lease-file.json')) as fp:
        expected = json.load(fp)
    n.assert_list_equal(observed, expected)
