from config import parser
from flask import g
from app import app
from updater import DhcpdUpdater

def main():
    config = parser.parse_args()
    updater = DhcpdUpdater(config.lease_file, config.timeout, config.lease_offset)
    updater.start()
    app.updater = updater
    app.run('0.0.0.0', config.port, debug=config.debug)
