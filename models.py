#!/usr/bin/env python
# coding: utf-8

import tornado.web
import tornado.gen
import json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from settings import redisKeys
from os.path import basename, expanduser

class Message(object):
    def __init__(self, *args, **kwargs):
        self.httpClient = AsyncHTTPClient()
        self._title = kwargs.get("title", "")
        self._content = kwargs.get("content", "")

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
    def __init__(self, redisConn, title="", content="", **qywxSettings):
        super(WeiXinQYMessage, self).__init__(title, content)
        self.baseUrl = qywxSettings.get("baseUrl")
        self.corpid = qywxSettings.get("corpid")
        self.corpsecret = qywxSettings.get("corpsecret")
        self.agentid = qywxSettings.get("agentid")
        self.toUser = qywxSettings.get("toUser")
        self.toParty = qywxSettings.get("toParty")
        self.timeout = qywxSettings.get("timeout")
        self.__redis = redisConn

    @tornado.gen.coroutine
    def refreshToken(self):
        request = HTTPRequest(
            url=self.baseUrl + '/gettoken?corpid=%s&corpsecret=%s' %
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
        if len(accessToken) == 0: return None
        body = {
            "touser": self.toUser,
            "toparty": self.toParty,
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
            url = self.baseUrl + "/message/send?access_token=%s" % accessToken,
            headers = {"Content-type": "application/json"},
            method = "POST",
            request_timeout = self.timeout,
            body = body
        )
        try:
            yield self.httpClient.fetch(request)
        except HTTPError:
            '''token过期返回：40014, 42001'''
            print("[Http error] response code: %s, reason: %s, fail to send msg.")

class SMSMessage(Message):
    def __init__(self, baseUrl, bodyDict, **kwargs):
        super(SMSMessage, self).__init__(**kwargs)
        self.baseUrl = baseUrl
        self.jsonBody = json.dumps(bodyDict)
        self.timeout = kwargs.get("timeout", 5)

    @tornado.gen.coroutine
    def send(self):
        url = "%s/sendsms"%self.baseUrl
        request = HTTPRequest(
            url = url,
            headers = {"Content-type": "application/json"},
            method = "POST",
            request_timeout = self.timeout,
            body = self.jsonBody
        )
        try:
            response = yield self.httpClient.fetch(request)
        except HTTPError:
            print("[Http error] response code: %s, reason: %s, fail to send sms." %
                  (response.code, response.reason))

class EmailMessage(Message):
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    def __init__(self, smtp, subject, fromAddress, toAddressList,
                 ccAddressList=[], defaultSign="", **kwargs):
        """
        subject(str): 邮件主题
        fromAddress(str): 发送人email
        toAddressList(list): 收件人列表
        ccAddressList(list): 抄送列表
        defaultSign(str): 默认签名
        """
        super(EmailMessage, self).__init__(**kwargs)
        self.subject = subject
        self.fromAddress = fromAddress
        self.toAddressList = toAddressList
        self.ccAddressList = ccAddressList
        self.defaultSign = defaultSign
        self.__smtp = smtp
        self._msg = self.MIMEMultipart()

    def addAttach(self, attachList):
        """
        添加邮件附件
        attach_list(list):附件文件名列表
        """
        for file in attachList:
            file = expanduser(file)
            part = self.MIMEBase('application', 'octet-stream')
            with open(file,'rb') as fp:
                part.set_payload(fp.read())
            self.encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=basename(expanduser(file)))
            self._msg.attach(part)

    def addMessage(self, content, type="plain"):
        """
        用于添加简单邮件内容,仅支持text和html内容
        """
        part = self.MIMEText(content, _subtype=type, _charset="utf-8")
        self._msg.attach(part)

    def addMessageFromFile(self, filename, type="plain", cid=""):
        """
        添加邮件内容
        filename(str): 邮件内容,从filename指定的文件中获取
        type(str):
            "text": 文本
            "html": html
            "image": 图片
            "cid": 基于html格式展示图片时,<img src="cid:xxx">需要使用cid
        """
        filename = expanduser(filename)
        if type in ("plain", "html"):
            fp = open(filename)
            part = self.MIMEText(fp.read(), _subtype=type, _charset="utf-8")
            fp.close()
        elif type == "image":
            fp = open(filename, 'rb')
            part = self.MIMEImage(fp.read())
            part.add_header("Content-ID", cid)
            fp.close()
        else:
            return
        self._msg.attach(part)

    def addSign(self, text, image=None):
        """
        添加邮件签名
        text(str): 签名的文本部分
        image(str): 图片文件名,签名的图片部分
        """
        self.addMessage(text, type="html")
        if image:
            self.addMessageFromFile(image, type="image")

    @tornado.gen.coroutine
    def send(self):
        self._msg["Subject"] = self.subject
        self._msg["From"] = self.fromAddress
        if isinstance(self.toAddressList, list):
            self._msg["To"] = ", ".join(self.toAddressList)
        elif isinstance(self.toAddressList, str):
            self.toAddressList = [ self.toAddressList ]
            self._msg["To"] = ", ".join(self.toAddressList)
        else:
            return
        if isinstance(self.ccAddressList, list):
            self._msg["CC"] = ", ".join(self.ccAddressList)
        elif isinstance(self.ccAddressList, str):
            self.ccAddressList = [ self.ccAddressList ]
            self._msg["CC"] = ", ".join(self.ccAddressList)
        else:
            self.ccAddressList = []
        self.addSign(self.defaultSign)
        yield self.__smtp.sendmail(self.fromAddress, self.toAddressList+self.ccAddressList, self._msg.as_string())
        self.__smtp.quit()