#!/usr/bin/env python
# coding: utf-8

import tornado.ioloop
import settings
from tornado.web import Application
from settings import routers, appSettings

def make_app(routers, **kwargs):
    return Application(routers, **kwargs)

if __name__ == "__main__":
    app = make_app(routers, **appSettings)
    app.listen(settings.port, address=settings.address)
    tornado.ioloop.IOLoop.current().start()