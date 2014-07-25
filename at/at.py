from wsgiref import simple_server

from config import parser
config = parser.parse_args()

def main():
    updater = DhcpdUpdater(config.lease_file, config.timeout, config.lease_offset)
    updater.start()
    app.run('0.0.0.0', config.port, debug=config.debug)
