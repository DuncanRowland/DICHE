import tornado.httpserver
import tornado.ioloop
import tornado.web
import requests
import json
import urllib
from secrets import APP_KEY,APP_SECRET,COOKIE_SECRET

class RobotsHandler(tornado.web.RequestHandler):
   def get(self):
      self.write("User-agent: *\r\nDisallow: /\r\n");

class AuthCallbackHandler(tornado.web.RequestHandler):
    def get(self):
        code=self.get_argument('code',default=None)
        if code==None:
            self.redirect("http://diche-app.eu.org")
        else:
            url="https://api.dropbox.com/1/oauth2/token"
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
                    }
            data={
                "grant_type":"authorization_code",
                "code":code,
                "redirect_uri":"https://diche-app.eu.org:8888/authcallback",
                 }
            r=requests.post(url, headers=headers, data=urllib.parse.urlencode(data), auth=(APP_KEY, APP_SECRET))
            o=json.loads(r.text)
            self.set_secure_cookie("token", o['access_token'])
            self.redirect("http://diche-app.eu.org/inituser")

def make_app():
    return tornado.web.Application([
        (r"/robots.txt", RobotsHandler),
        (r"/authcallback", AuthCallbackHandler),
    ],debug=True, cookie_secret=COOKIE_SECRET)

if __name__ == "__main__":
    app = make_app()
    https_server=tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": "keys/cert.pem",
        "keyfile": "keys/key.pem",
    })
    https_server.listen(8888)
    tornado.ioloop.IOLoop.current().start()

