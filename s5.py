# -*- coding:UTF-8 -*-


import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.concurrent import Future


future = None
class MainHandler(tornado.web.RequestHandler):
    '''
    手写future，future的功能：
    1,可以挂起当前请求，线程可以处理其他的请求****异步非阻塞
     2， future设置值，当前的挂起请求就返回了
    '''
    # 请求来永远的挂起，等待某一时刻，主动给future设置上值
    @gen.coroutine
    def get(self):
        global future
        future = Future()
        future.add_done_callback(self.done)
        yield future

    def done(self,*args,**kwargs):
        self.write('Main')
        self.finish()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        global future
        # 当前请求处理了，挂起的那个请求也释放了
        future.set_result(None)
        self.write("Index")

application = tornado.web.Application([
    (r"/main", MainHandler),
    (r'/index',IndexHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()




















