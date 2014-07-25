from datetime import datetime
from time import mktime

from iscpy import ParseISCString

def lease_file(fp, lease = False):
    leases = ParseISCString(fp.read())
    for l in leases:
        lease = l.values()[0]

        ip = lease.keys()[0].split(' ')[1]

        hwaddr = lease['hardware'].split(' ')[1]

        _starts = datetime.strptime(lease['starts'][2:], '%Y/%m/%d %H:%M:%S;')
        atime = mktime(dt.utctimetuple())

        if 'client-hostname' in lease:
            name = lease['client-hostname'][1][1:-2]
        else:
            name = None
        yield (hwaddr, atime, ip, name)
