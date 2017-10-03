from local_settings import *
from views import *
from tornado.web import url

routers = [
    url(r"^/?$", IndexHandler, name="index"),
    url(r"^/qywx/?", WeiXinQYHandler, name="qywx"),
    url(r"^/sms/?", SMSHandler, name="sms"),
    url(r"^/mail/?", EmailHandler, name="mail"),
]

appSettings = {
    "debug": False,
}

