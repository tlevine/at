from datetime import datetime
from time import time

#@app.template_filter('strfts')
def strfts(ts, format='%d/%m/%Y %H:%M'):
    return datetime.fromtimestamp(ts).strftime(format)

def fake_now_at(_, db):
    users = [
        ('this-owner', time() - 18 * 60),
        ('that-owner', time() - 24 * 60),
    ]
    unknown = {'another-hwaddr', 'yet-another-hwaddr'}
    return dict(users=users, unknown=unknown)
