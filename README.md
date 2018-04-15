



# 自定义异步非阻塞Web框架

### 支持异步非阻塞Web框架-- Tornado，Nodejs

- 异步IO模块：
    我们作为客户端向服务端发起“并发”请求，select监听socket是否已经有变化
    future= Future（）主要的
    1. 挂起当前请求，线程可以处理其他请求
    2. future设置值，当前挂起的请求返回

- IO请求不占CPU，计算型需要使用CPU


- 自定义web框架
    - 同步
        - 从Socket开始
        - 使用IO多路复用，当不发请求的时候，其他的可以过来，只是监听有没有变化
        - 步骤：
            - 请求头中获取url，将其处理为字典格式
            - 去路由中匹配，获取指定的函数
            - 执行函数，获取返回值
            - 将返回值send回去
    - 异步
        - 使用Future（）对象，只要是future对象，来一个请求，只要future的result里面还没有给值，就可以将该请求挂起，仍然可以执行其他的请求，当future对象设置了值的时候，表示该请求结束，断开连接
        - 使用Future()对象，通过设置超时时间来判断请求是否断开，当请求到来时，不用管它，可以处理其他的请求，当连接的时间超过了预先设定的超时时间的时候，主动断开连接，结束请求，将socket移除

说明：[详细的WebSocket讲解地址](https://yuansuixin.github.io/ "详细的WebSocket讲解地址")


### 使用

1.基本使用

```
from snow import Snow
from snow import HttpResponse
 
 
def index(request):
    return HttpResponse('OK')
 
 
routes = [
    (r'/index/', index),
]
 
app = Snow(routes)
app.run(port=8012)
```

2. 异步非阻塞：超时

```
from snow import Snow
from snow import HttpResponse
from snow import TimeoutFuture
 
request_list = []
 
 
def async(request):
    obj = TimeoutFuture(5)
    yield obj
 
 
def home(request):
    return HttpResponse('home')
 
 
routes = [
    (r'/home/', home),
    (r'/async/', async),
]
 
app = Snow(routes)
app.run(port=8012)
```

3. 异步非阻塞，等待
  基于等待模式可以完成自定制操作

```
from snow import Snow
from snow import HttpResponse
from snow import Future
 
request_list = []
 
 
def callback(request, future):
    return HttpResponse(future.value)
 
 
def req(request):
    obj = Future(callback=callback)
    request_list.append(obj)
    yield obj
 
 
def stop(request):
    obj = request_list[0]
    del request_list[0]
    obj.set_result('done')
    return HttpResponse('stop')
 
 
routes = [
    (r'/req/', req),
    (r'/stop/', stop),
]
 
app = Snow(routes)
app.run(port=8012)
```

### 源码

[源码下载](https://github.com/yuansuixin/Tornado-Asynchronous-non-blocking "源码下载")


```
#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import socket
import select
import time


class HttpResponse(object):
    """
    封装响应信息
    """
    def __init__(self, content=''):
        self.content = content

        self.headers = {}
        self.cookies = {}

    def response(self):
        return bytes(self.content, encoding='utf-8')


class HttpNotFound(HttpResponse):
    """
    404时的错误提示
    """
    def __init__(self):
        super(HttpNotFound, self).__init__('404 Not Found')


class HttpRequest(object):
    """
    用户封装用户请求信息
    """
    def __init__(self, conn):
        self.conn = conn

        self.header_bytes = bytes()
        self.header_dict = {}
        self.body_bytes = bytes()

        self.method = ""
        self.url = ""
        self.protocol = ""

        self.initialize()
        self.initialize_headers()

    def initialize(self):

        header_flag = False
        while True:
            try:
                received = self.conn.recv(8096)
            except Exception as e:
                received = None
            if not received:
                break
            if header_flag:
                self.body_bytes += received
                continue
            temp = received.split(b'\r\n\r\n', 1)
            if len(temp) == 1:
                self.header_bytes += temp
            else:
                h, b = temp
                self.header_bytes += h
                self.body_bytes += b
                header_flag = True

    @property
    def header_str(self):
        return str(self.header_bytes, encoding='utf-8')

    def initialize_headers(self):
        headers = self.header_str.split('\r\n')
        first_line = headers[0].split(' ')
        if len(first_line) == 3:
            self.method, self.url, self.protocol = headers[0].split(' ')
            for line in headers:
                kv = line.split(':')
                if len(kv) == 2:
                    k, v = kv
                    self.header_dict[k] = v


class Future(object):
    """
    异步非阻塞模式时封装回调函数以及是否准备就绪
    """
    def __init__(self, callback):
        self.callback = callback
        self._ready = False
        self.value = None

    def set_result(self, value=None):
        self.value = value
        self._ready = True

    @property
    def ready(self):
        return self._ready


class TimeoutFuture(Future):
    """
    异步非阻塞超时
    """
    def __init__(self, timeout):
        super(TimeoutFuture, self).__init__(callback=None)
        self.timeout = timeout
        self.start_time = time.time()

    @property
    def ready(self):
        current_time = time.time()
        if current_time > self.start_time + self.timeout:
            self._ready = True
        return self._ready


class Snow(object):
    """
    微型Web框架类
    """
    def __init__(self, routes):
        self.routes = routes
        self.inputs = set()
        self.request = None
        self.async_request_handler = {}

    def run(self, host='localhost', port=9999):
        """
        事件循环
        :param host:
        :param port:
        :return:
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port,))
        sock.setblocking(False)
        sock.listen(128)
        sock.setblocking(0)
        self.inputs.add(sock)
        try:
            while True:
                readable_list, writeable_list, error_list = select.select(self.inputs, [], self.inputs,0.005)
                for conn in readable_list:
                    if sock == conn:
                        client, address = conn.accept()
                        client.setblocking(False)
                        self.inputs.add(client)
                    else:
                        gen = self.process(conn)
                        if isinstance(gen, HttpResponse):
                            conn.sendall(gen.response())
                            self.inputs.remove(conn)
                            conn.close()
                        else:
                            yielded = next(gen)
                            self.async_request_handler[conn] = yielded
                self.polling_callback()

        except Exception as e:
            pass
        finally:
            sock.close()

    def polling_callback(self):
        """
        遍历触发异步非阻塞的回调函数
        :return:
        """
        for conn in list(self.async_request_handler.keys()):
            yielded = self.async_request_handler[conn]
            if not yielded.ready:
                continue
            if yielded.callback:
                ret = yielded.callback(self.request, yielded)
                conn.sendall(ret.response())
            self.inputs.remove(conn)
            del self.async_request_handler[conn]
            conn.close()

    def process(self, conn):
        """
        处理路由系统以及执行函数
        :param conn:
        :return:
        """
        self.request = HttpRequest(conn)
        func = None
        for route in self.routes:
            if re.match(route[0], self.request.url):
                func = route[1]
                break
        if not func:
            return HttpNotFound()
        else:
            return func(self.request)

snow.py

```















