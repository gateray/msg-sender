# 概述

> msg-sender是一个基于tornado框架的异步消息发送接口，当前支持消息发送微信企业号、玄武短信接口和Email; 接口调用支持http和websocket。遵循MIT开源许可。

# 接口调用方式

## 微信企业号消息发送接口

关闭签名：

字段名 | 字段类型 | 是否必须 | 描述
-----------|-----------|-----------|-----------
title | String | 是 | 消息的标题
content | String | 是 | 消息的内容

```
POST http://host:8000/qywx?content=abc&title=接口测试
```

开启签名：

字段名 | 字段类型 | 是否必须 | 描述
-----------|-----------|-----------|-----------
title | String | 是 | 消息的标题
content | String | 是 | 消息的内容
timestamp | Integer | 是 | unix时间戳（当前时间，10位数字）
signature | String | 是 | 16进制格式的签名值,支持md5、sha1、sha128、sha224、 sha256、 sha384、 sha512签名方法，默认为sha256。

签名说明：

* 将所有字段按key自然排序后，拼接key-value得到字符串A

* 字符串A后拼接上apiKey，得到字符串B

* 字符串B进行签名，输出的16进制字符串为signature字段的值

示例：

* 假设title=test&content=test消息内容&timestamp=1507545674， apiKey=mysecret

* 按key自然排序的结果为：content=test消息内容&timestamp=1507545674&title=test

* 拼接后得到字符串：contenttest消息内容timestamp1507545674titletest

* 拼接上apiKey得到的字符串：contenttest消息内容timestamp1507545674titletestmysecret

* 上一步得到的字符串进行sha256签名，得到签名：28924486d2aaf886565736a50e61bb9fb0d3baf613e2333b0e497934699ec15b

```
POST http://host:8000/qywx?title=test&content=test消息内容&timestamp=1507545674&signature=28924486d2aaf886565736a50e61bb9fb0d3baf613e2333b0e497934699ec15b
```

> 签名有效期为1分钟

## 玄武短信消息发送接口

关闭签名：

字段名 | 字段类型 | 是否必须 | 描述
----------|--------------|--------------|-------
title | String | 是 | 消息的标题
content | String | 是 | 消息的内容

```
POST http://host:8000/sms?content=这是一条测试短信&title=标题会忽略
```

开启签名：

规则与上面微信企业号方式相同

## Email消息发送接口

关闭签名：

字段名 | 字段类型 | 是否必须 | 描述
----------|-------------|--------------|-------
title | String | 是 | 消息的标题
content | String | 是 | 消息的内容

```
POST http://host:8000/mail?content=这是一封测试邮件，请勿回复！&title=接口测试
```

开启签名：

规则与上面微信企业号方式相同

# 部署

## 环境要求

* python 3.5以上

* redis 2.8以上（可选，使用微信企业号发送消息时需要使用）

* 推荐linux环境下运行

## 依赖安装

```
git clone https://github.com/gateray/msg-sender.git
cd msg-sender
pip install -r requirements.txt
```

## 运行

### 测试环境

```
cp local_settings.py.example local_settings.py
python app.py --port=8000
```

### 生产环境部署建议

建议使用nginx作为反向代理，后端开启多个python进程(建议与cpu核数相等)做负载均衡。

#### 打开最多文件数限制：

方式一：

```
ulimit -n 1048576
```

方式二：

```
vim /etc/security/limits.conf
# 加上下面配置：
* - nofile 1048576
```

方式三（systemd）：

```
在对应服务的service文件中添加，例如：
vim /lib/systemd/system/nginx.service
[Service]
User=gateray
Group=gateray
LimitNOFILE= 1048576
# 实际上对于nginx，可以通过配置文件中 worker_connections  1048576;指定
```

#### 开启多个python进程：

```
for i in {8001..8008}; do
    nohup python app.py --port=800$i &> /tmp/msg-sender-800$i.log &
done
```

强烈推荐使用supervisor去管理进程，以下是一个示例：

```
➜  msg-sender git:(master) ✗ cat /etc/supervisord.conf.d/msg-sender.conf

[program:msg-sender-8001]

directory=/home/gateray/workspace/python/msg-sender

command=/home/gateray/.virtualenvs/msg-sender/bin/python app.py --port=8001

process_name=%(program_name)s                  ; process_name expr (default %(program_name)s)

user=gateray                                   ; setuid to this UNIX account to run the program

redirect_stderr=true                           ; redirect proc stderr to stdout (default false)

stdout_logfile=/tmp/%(program_name)s.log       ; stdout log path, NONE for none; default AUTO



[program:msg-sender-8002]

directory=/home/gateray/workspace/python/msg-sender

command=/home/gateray/.virtualenvs/msg-sender/bin/python app.py --port=8002

process_name=%(program_name)s                  ; process_name expr (default %(program_name)s)

user=gateray                                   ; setuid to this UNIX account to run the program

redirect_stderr=true                           ; redirect proc stderr to stdout (default false)

stdout_logfile=/tmp/%(program_name)s.log       ; stdout log path, NONE for none; default AUTO



[program:msg-sender-8003]

directory=/home/gateray/workspace/python/msg-sender

command=/home/gateray/.virtualenvs/msg-sender/bin/python app.py --port=8003

process_name=%(program_name)s                  ; process_name expr (default %(program_name)s)

user=gateray                                   ; setuid to this UNIX account to run the program

redirect_stderr=true                           ; redirect proc stderr to stdout (default false)

stdout_logfile=/tmp/%(program_name)s.log       ; stdout log path, NONE for none; default AUTO



[program:msg-sender-8004]

directory=/home/gateray/workspace/python/msg-sender

command=/home/gateray/.virtualenvs/msg-sender/bin/python app.py --port=8004

process_name=%(program_name)s                  ; process_name expr (default %(program_name)s)

user=gateray                                   ; setuid to this UNIX account to run the program

redirect_stderr=true                           ; redirect proc stderr to stdout (default false)

stdout_logfile=/tmp/%(program_name)s.log       ; stdout log path, NONE for none; default AUTO

```

#### nginx配置：

```

user  gateray;

worker_processes  4;

events {

    worker_connections  1048576;

}

http {

    include       mime.types;

    default_type  application/octet-stream;

    upstream msg-senders {

        server 127.0.0.1:8001;

        server 127.0.0.1:8002;

        server 127.0.0.1:8003;

        server 127.0.0.1:8004;

    }

    sendfile        on;

    keepalive_timeout  65;

    gzip  on;

    server {

        listen       80;

        server_name  localhost;



        charset utf-8;

        location / {

            root   html;

            index  index.html index.htm;

        }

        location /msg-sender/ {

            proxy_pass http://msg-senders/;

        }

        #error_page  404              /404.html;

        error_page   500 502 503 504  /50x.html;

        location = /50x.html {

            root   html;

        }

    }

}

```

# 本地压测结果：

```

➜  aliyun ulimit -n 1048576

➜  aliyun ab -k -n 1000000 -c 5000 http://localhost/

This is ApacheBench, Version 2.3 <$Revision: 1706008 $>

Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/

Licensed to The Apache Software Foundation, http://www.apache.org/



Benchmarking localhost (be patient)

Completed 100000 requests

Completed 200000 requests

Completed 300000 requests

Completed 400000 requests

Completed 500000 requests

Completed 600000 requests

Completed 700000 requests

Completed 800000 requests

Completed 900000 requests

Completed 1000000 requests

Finished 1000000 requests





Server Software:        openresty/1.11.2.5

Server Hostname:        localhost

Server Port:            80



Document Path:          /

Document Length:        562 bytes



Concurrency Level:      5000

Time taken for tests:   24.663 seconds

Complete requests:      1000000

Failed requests:        0

Keep-Alive requests:    991975

Total transferred:      805959875 bytes

HTML transferred:       562000000 bytes

Requests per second:    40546.28 [#/sec] (mean)

Time per request:       123.316 [ms] (mean)

Time per request:       0.025 [ms] (mean, across all concurrent requests)

Transfer rate:          31912.76 [Kbytes/sec] received



Connection Times (ms)

              min  mean[+/-sd] median   max

Connect:        0    3  67.1      0    3080

Processing:     0  120  71.5    119    1010

Waiting:        0  119  71.5    118    1010

Total:          0  123 100.1    167    3370



Percentage of the requests served within a certain time (ms)

  50%    167

  66%    185

  75%    187

  80%    188

  90%    191

  95%    194

  98%    197

  99%    199

 100%   3370 (longest request)

```

每秒可处理40k个请求



# 联系方式

QQ：437925289

Email：437925289@qq.com
