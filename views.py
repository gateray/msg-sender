#!/usr/bin/env python
# coding: utf-8

import tornado.gen
from tornado.web import RequestHandler
from settings import *
from models import WeiXinQYMessage


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
                #获取签名
                signature = argsDict.pop('signature', None)
                assert signature, "missing signature."
                signature = signature[0].decode()
                #按key自然排序，合并所有key、value
                combineStr = "".join([ "%s%s"%(k,argsDict[k][0].decode()) for k in sorted(argsDict)]) + apiKey
                #验证签名
                assert (hashdigest(combineStr) == signature), "signature not match."
                #验证时间戳
                import time
                if (time.time() - signatureTimeOutSecs) > int(argsDict['timestamp'][0]):
                    raise Exception("signature has expired.")




class IndexHandler(RequestHandler):
    def get(self):
        self.write("it works!")

class WeiXinQYHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        weiXinQYMessage = WeiXinQYMessage(**qywx)
        weiXinQYMessage.title = self.get_argument('title', "")
        weiXinQYMessage.content = self.get_argument('content', "")
        yield weiXinQYMessage.send()
        self.write("ok")