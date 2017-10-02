#!/usr/bin/env python
# coding: utf-8

import tornadoredis
import tornado.web
import tornado.gen
import json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from settings import redis, redisKeys

class Message(object):
    def __init__(self, *args, **kwargs):
        self._title = kwargs.get("title", None)
        self._content = kwargs.get("content", None)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        self._content = content

    def send(self):
        pass


class WeiXinQYMessage(Message):
    __redis = tornadoredis.Client(host=redis["host"], port=redis["port"], selected_db=redis["db"])
    __redis.connect()
    def __init__(self, **qywxSettings):
        super(WeiXinQYMessage, self).__init__(**qywxSettings)
        self.apiHost = qywxSettings.get("apiHost")
        self.corpid = qywxSettings.get("corpid")
        self.corpsecret = qywxSettings.get("corpsecret")
        self.agentid = qywxSettings.get("agentid")
        self.timeout = qywxSettings.get("timeout")
        self.httpClient = AsyncHTTPClient()

    @tornado.gen.coroutine
    def refreshToken(self):
        request = HTTPRequest(
            url=self.apiHost + '/cgi-bin/gettoken?corpid=%s&corpsecret=%s' %
                               (self.corpid, self.corpsecret),
            method='GET',
            request_timeout=self.timeout
        )
        try:
            response = yield self.httpClient.fetch(request)
        except HTTPError:
            print("[Http error] response code: %s, reason: %s, fail to get access_token." %
                  (response.code, response.reason))
            return ""
        try:
            accessToken = json.loads(response.body).get("access_token")
            yield tornado.gen.Task(self.__redis.setex, redisKeys["WXQY_ACCESS_TOKEN"], 7200, accessToken)
            return accessToken
        except json.JSONDecodeError:
            print("JSON decode error, fail to get access_token.")
            return ""
        except Exception as e:
            print(str(e))
            return ""

    @tornado.gen.coroutine
    def getAccessToken(self):
        try:
            accessToken = yield tornado.gen.Task(self.__redis.get, redisKeys["WXQY_ACCESS_TOKEN"])
        except Exception as e:
            print(str(e))
            accessToken = ""
        if not accessToken:
            accessToken = yield self.refreshToken()
        return accessToken

    @tornado.gen.coroutine
    def send(self):
        accessToken = yield self.getAccessToken()
        print(accessToken)
        return
        if len(accessToken) == 0: return None
        body = {
            "touser": "gateray",
            "toparty": "",
            "totag": "",
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": "[%s]\n%s"%(self.title,self.content)
            },
            "safe": 0
        }
        body = json.dumps(body)
        request = HTTPRequest(
            url = self.apiHost + "/cgi-bin/message/send?access_token=%s" % accessToken,
            headers = {"Content-type": "application/json"},
            method = "POST",
            request_timeout = 5,
            body = body
        )
        try:
            yield self.httpClient.fetch(request)
        except HTTPError:
            '''token过期返回：40014, 42001'''
            print("[Http error] response code: %s, reason: %s, fail to send msg.")

