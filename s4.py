# -*- coding:UTF-8 -*-


import tornado.ioloop
import tornado.web
from tornado import gen

# tornado支持发送异步IO模块，发送http请求的时候，也可以异步非阻塞处理其他事情
class MainHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        from tornado import httpclient
        http = httpclient.AsyncHTTPClient()
        # 在内部创建了future对象，_result里面也是没有值的，检测到有值的时候断开连接
        yield http.fetch('http://www.google.com',self.done)

    def done(self,*args,**kwargs):
        self.write('Main')
        self.finish()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Index")

application = tornado.web.Application([
    (r"/main", MainHandler),
    (r'/index',IndexHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()




















