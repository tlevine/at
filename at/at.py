from config import parser
from app import configure_app
from updater import DhcpdUpdater

def main():
    config = parser.parse_args()
    updater = DhcpdUpdater(config.lease_file, config.timeout, config.lease_offset)
    updater.start()
    app = configure_app(config, updater)
    app.run('0.0.0.0', config.port, debug=config.debug)
