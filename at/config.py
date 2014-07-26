import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action = 'store_false')
parser.add_argument('--port', default = 8080, type = int)
parser.add_argument('--db', default = './at.db')
parser.add_argument('--cap-file', default = './dhcp-cap')
parser.add_argument('--lease-file', default = './leases')
parser.add_argument('--lease-offset', help = 'Lease offset, in seconds',
    type = lambda x: int(x) * 60, default = 20)
parser.add_argument('--timeout', default = 3000, type = int)
parser.add_argument('--wiki-url', default = 'http://hackerspace.pl/wiki/doku.php?id=people:%(login)s:start')
parser.add_argument('--secret-key', default = 'adaba')
parser.add_argument('--claimable-prefix', default = '',
    help = 'You might switch this for "192.168.1", for example.')
parser.add_argument('--claimable-exclude', metavar = '[exclude]', nargs = '+',
    help = 'For example, "127.0.0.1"')
parser.add_argument('--fake', action = 'store_true',
    help = 'Fake the active device list (for development).')
