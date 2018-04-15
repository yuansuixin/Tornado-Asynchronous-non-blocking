import socket
import select

'''
自定义异步Web框架
通过判断future对象中有无值来判断是否结束请求
'''

class HttpRequest(object):
    """
    用户封装用户请求信息
    """
    def __init__(self, content):
        """

        :param content:用户发送的请求数据：请求头和请求体
        """
        self.content = content

        self.header_bytes = bytes()
        self.body_bytes = bytes()

        self.header_dict = {}

        self.method = ""
        self.url = ""
        self.protocol = ""

        self.initialize()
        self.initialize_headers()
    # 处理请求信息
    def initialize(self):
        temp = self.content.split(b'\r\n\r\n', 1)
        if len(temp) == 1:
            self.header_bytes += temp
        else:
            h, b = temp
            self.header_bytes += h
            self.body_bytes += b

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

# 异步非阻塞最重要的成分
class Future(object):
    def __init__(self):
        self.result = None


F = None
def main(request):
    global F
    F = Future()
    return F

def stop(request):
    global F
    F.result = b"xxxxxxxxxxxxx"
    return "stop"


def index(request):
    return "indexasdfasdfasdf"


routers = [
    ('/main/',main),
    ('/index/',index),
    ('/stop/',stop),
]

def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 9999,))
    sock.setblocking(False)
    sock.listen(128)

    inputs = []
    inputs.append(sock)

    async_request_dict = {
        # 'socket': futrue
    }

    while True:
        rlist,wlist,elist = select.select(inputs,[],[],0.05)
        # 只处理请求来时返回的内容，异步的时候将yield添加到列表中
        for r in rlist:
            if r == sock:
                """新请求到来"""
                conn,addr = sock.accept()
                conn.setblocking(False)
                inputs.append(conn)
            else:
                """客户端发来数据"""
                data = b""
                while True:
                    try:
                        chunk = r.recv(1024)
                        data = data + chunk
                    except Exception as e:
                        chunk = None
                    if not chunk:
                        break
                # data进行处理：请求头和请求体
                request = HttpRequest(data)
                # 1. 请求头中获取url
                # 2. 去路由中匹配，获取指定的函数
                # 3. 执行函数，获取返回值
                # 4. 将返回值 r.sendall(b'alskdjalksdjf;asfd')
                import re
                flag = False
                func = None
                for route in routers:
                    if re.match(route[0],request.url):
                        flag = True
                        func = route[1]
                        break
                if flag:
                    result = func(request)
                    # 如果result是future对象，将socket写入到字典里，否则，做返回处理
                    if isinstance(result,Future):
                        async_request_dict[r] = result
                    else:
                        r.sendall(bytes(result,encoding='utf-8'))
                        inputs.remove(r)
                        r.close()
                else:
                    r.sendall(b"404")
                    inputs.remove(r)
                    r.close()

        for conn in async_request_dict.keys():
            future = async_request_dict[conn]
            if future.result:
                # future设置了值，那么请求结束，断开连接，并将连接删除，移除socket
                conn.sendall(future.result)
                conn.close()
                del async_request_dict[conn]
                inputs.remove(conn)

if __name__ == '__main__':
    run()