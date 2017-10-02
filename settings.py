from local_settings import *
from views import *
from tornado.web import url

routers = [
    url(r'^/?$', IndexHandler, name="index"),
    url(r'^/wxqy/?', WeiXinQYHandler, name='wxqy'),
]

appSettings = {
    "debug": False,
}

