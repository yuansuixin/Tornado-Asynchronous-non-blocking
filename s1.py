# -*- coding:UTF-8 -*-


import tornado.ioloop
import tornado.web

# 同步型的，两个请求必须等待第一个请求处理完才可以处理第二个请求
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        import time
        time.sleep(10)
        self.write("Main")

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




















