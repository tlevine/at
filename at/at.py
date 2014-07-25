#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import threading
import traceback
import json
from werkzeug.contrib.fixers import ProxyFix
from wsgiref import simple_server
from pesto import Response, dispatcher_app
from time import sleep, time, mktime
from collections import namedtuple
from urllib import urlencode
from hashlib import sha256

import parse
from config import parser
config = parser.parse_args()

updater = None



def main():
    updater = DhcpdUpdater(config.lease_file, config.timeout, config.lease_offset)
    updater.start()
    app.run('0.0.0.0', config.port, debug=config.debug)
