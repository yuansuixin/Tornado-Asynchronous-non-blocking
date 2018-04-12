# -*- coding:UTF-8 -*-


import tornado.ioloop
import tornado.web
import time
from tornado import gen
from tornado.concurrent import Future

'''
tornado异步非阻塞形式
'''
# 请求先来，等5s再返回，在等待的这5s内可以处理其他的请求
class MainHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        # 看着future没有用到，其实future用到了，在Future类中有个_result
        # 原理：web框架会监听返回的future，检测_result有没有值，如果没有值，当前的链接就不断开，
        # 说明还没有处理完，如果有值了，就断开，执行以下回调函数就断开了
        future = Future()
        # 特殊的形式模拟等待5s
        tornado.ioloop.IOLoop.current().add_timeout(time.time()+5,self.done)
        yield future

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




















