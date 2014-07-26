from datetime import datetime
from time import time
from queries import User

def strfts(ts, format='%d/%m/%Y %H:%M'):
    return datetime.fromtimestamp(ts).strftime(format)

def fake_now_at(_, db):
    t = lambda: strfts(time())
    this_owner = User(8, 'this-owner', 'this-password', 'http://this.url')
    that_owner = User(25, 'that-owner', 'that-password', 'http://that.url')
    return [
        (this_owner, 'a-claimed-hwaddr', t() - 18 * 60),
        (this_owner, 'another-claimed-hwaddr', t() - 17 * 60),
        (that_owner, 'yet-another-claimed-hwaddr', t() - 24 * 60),
        (None, 'unclaimed-hwaddr', '192.168.1.102', t() - 15 * 60),
        (None, 'another-unclaimed-hwaddr', '192.168.1.106', t() - 13 * 60),
    ]
