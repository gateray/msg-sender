#!/usr/bin/env python
# coding: utf-8

import tornado.gen
from tornado.web import RequestHandler
from settings import *
from models import WeiXinQYMessage, SMSMessage, EmailMessage
from tornado.websocket import WebSocketHandler
from datetime import datetime

class BaseHandler(RequestHandler):
    def prepare(self):
        def hashdigest(text):
            import hashlib
            algo = None
            if signatureMethod in signatureSupportList:
                algo = getattr(hashlib, signatureMethod)
            assert algo, "%s signatureMethod is not support." % signatureMethod
            m = algo()
            byteText = text.encode() if isinstance(text, str) else text
            m.update(byteText)
            return m.hexdigest()

        if self.request.method == "POST":
            if enableSignature:
                #获取所有请求参数
                argsDict = self.request.arguments #{'timestamp': [b'12341234182'], 'test': [b'abc']}
                # 验证时间戳
                import time
                if (time.time() - signatureTimeOutSecs) > int(argsDict.get('timestamp', [0])[0]):
                    raise Exception("signature has expired.")
                #获取签名
                signature = argsDict.pop('signature', None)
                assert signature, "missing signature."
                signature = signature[0].decode()
                #按key自然排序，合并所有key、value
                combineStr = "".join([ "%s%s"%(k,argsDict[k][0].decode()) for k in sorted(argsDict)]) + apiKey
                #验证签名
                assert (hashdigest(combineStr) == signature), "signature not match."

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        yield self.write("it works!")

class IndexHandler(RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        yield self.write("it works!")

class WeiXinQYHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        title = self.get_argument("title", "")
        content = self.get_argument("content", "")
        weiXinQYMessage = WeiXinQYMessage(self.application.getRedisConn(),
                                          title=title, content=content, **qywx)
        yield weiXinQYMessage.send()
        self.write("ok")

class SMSHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        smsBody = sms.get("body")
        smsBody["text"] = self.get_argument("content", "")
        smsMessage = SMSMessage(sms["baseUrl"], smsBody, timeout=sms["timeout"])
        yield smsMessage.send()
        self.write("ok")

class EmailHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        content = self.get_argument("content", "")
        title = self.get_argument("title", "")
        emailMessage = EmailMessage(
            self.application.getSMTPConn(),
            subject=title,
            fromAddress=mail["fromAddress"],
            toAddressList=mail["toAddressList"],
            ccAddressList=mail["ccAddressList"],
            defaultSign=mail["defaultSign"]
        )
        emailMessage.addMessage(content, type="html")
        yield emailMessage.send()
        self.write("ok")

class WebSocketHandler(WebSocketHandler):
    users = set()

    def open(self):
        self.users.add(self)
        for u in self.users:
            u.write_message("[%s]-[%s]-login."%(self.request.remote_ip,
                                          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    def on_message(self, message):
        for u in self.users:
            u.write_message("[%s]-[%s]-send: %s"%(self.request.remote_ip,
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message))

    def on_close(self):
        self.users.remove(self)
        for u in self.users:
            u.write_message("[%s]-[%s]-logout."%(self.request.remote_ip,
                                          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    def check_origin(self, origin):
        return True