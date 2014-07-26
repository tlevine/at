from datetime import datetime
from time import time

def strfts(ts, format='%d/%m/%Y %H:%M'):
    return datetime.fromtimestamp(ts).strftime(format)

def fake_now_at(_, db):
    return [
        ('this-owner', 'a-claimed-hwaddr', time() - 18 * 60),
        ('that-owner', 'another-claimed-hwaddr', time() - 24 * 60),
        (None, 'unclaimed-hwaddr', '192.168.1.102', time() - 15 * 60),
        (None, 'another-unclaimed-hwaddr', '192.168.1.106', time() - 13 * 60),
    ]
