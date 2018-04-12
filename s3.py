# -*- coding:UTF-8 -*-


import tornado.ioloop
import tornado.web

# 同步型的
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        import requests
        requests.get('http://www.baidu.com')
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




















