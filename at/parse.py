from datetime import datetime
from time import mktime

from iscpy import ParseISCString

def lease_file(fp, lease = False):
    leases = ParseISCString(fp.read())
    for l in leases:
        ip = l.keys()[0].split(' ')[1]

        lease = l.values()[0]

        hwaddr = lease['hardware'].split(' ')[1]

        _starts = datetime.strptime(lease['starts'][2:], '%Y/%m/%d %H:%M:%S')
        atime = mktime(_starts.utctimetuple())

        if 'client-hostname' in lease:
            name = lease['client-hostname'][1][1:-2]
        else:
            name = None
        yield (hwaddr, atime, ip, name)
