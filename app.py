#!/usr/bin/env python
# coding: utf-8

import tornado.ioloop
from tornado.web import Application
from settings import *

def make_app(routers, **kwargs):
    class ExtApplication(Application):
        def __init__(self, routers, **kwargs):
            self.redisConn = None
            for urlSpec in routers:
                if urlSpec.name not in enableList:
                    routers.remove(urlSpec)
            super(ExtApplication, self).__init__(routers, **kwargs)
        def getRedisConn(self):
            try:
                import tornadoredis
                if self.redisConn is None:
                    redisConn = tornadoredis.Client(host=redis["host"], port=redis["port"], selected_db=redis["db"])
                    redisConn.connect()
                    self.redisConn = redisConn
                return self.redisConn
            except Exception:
                self.redisConn = None
                raise
        def getSMTPConn(self):
            try:
                import smtplib
                smtp = smtplib.SMTP()
                smtp.connect(mail["smtpServer"], mail["smtpPort"])
                # smtp.starttls()
                smtp.login(mail["username"], mail["password"])
                return smtp
            except Exception:
                if smtp:
                    smtp.close()
                raise

    return ExtApplication(routers, **kwargs)

if __name__ == "__main__":
    app = make_app(routers, **appSettings)
    app.listen(port, address=address)
    tornado.ioloop.IOLoop.current().start()