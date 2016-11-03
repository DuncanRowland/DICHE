import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.template
import tornado.options
import requests
import json
import os
import signal
import glob
import ffmpy
import time
import random
import subprocess
import logging
from secrets import APP_KEY,APP_SECRET,COOKIE_SECRET,ADMIN1,ADMIN2

class LandingHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader("templates")
        self.template_header = self.loader.load("header.html")
        self.template_splash = self.loader.load("splash.html")

    def get(self):
        token=self.get_secure_cookie('token')
        if token==None:
           self.write(self.template_header.generate())
           self.write(self.template_splash.generate())
        else:
           self.redirect("/settings")

class MenuHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.loader = tornado.template.Loader("templates")
        self.template_header = self.loader.load("header.html")
        self.template_menu = self.loader.load("menu.html")
        self.helptext_html = None
        self.enabled_menu_ids = set()

    def prepare(self):
        #Setup Member Variables
        _token=self.get_secure_cookie('token')
        if _token==None:
            self.redirect("/")
            return
        self.token = tornado.escape.to_basestring(_token)
        _familiar_name = self.get_secure_cookie('familiar_name')
        _account_id = self.get_secure_cookie('account_id')
        if _familiar_name==None or _account_id==None:
            r = self.dbpost("https://api.dropboxapi.com/2/users/get_current_account", data=None)
            if r.status_code!=200:
                self.clear_all_cookies()
                self.redirect("/")
                return
            o=json.loads(r.text)
            self.familiar_name = o["name"]["familiar_name"]
            self.set_secure_cookie('familiar_name',self.familiar_name)
            self.account_id = o["account_id"]
            self.set_secure_cookie('account_id',self.account_id)
        else:
            self.familiar_name = tornado.escape.to_basestring(_familiar_name)
            self.account_id = tornado.escape.to_basestring(_account_id)
        _selected_project = self.get_cookie("selected_project")
        if _selected_project:
            self.selected_project = tornado.escape.to_basestring(_selected_project)
            audiofile = "userfiles/"+self.account_id+"/"+self.selected_project+"/DICHE.mp3"
            self.audio_is_available = os.path.exists(audiofile)
        else:
            self.selected_project = None
            self.audio_is_available = False
            self.set_cookie('show_tutorials','true')
        _project_is_selected = not self.selected_project == None
        #Configure Menu 
        self.enabled_menu_ids = {'menuitem_settings','menuitem_logout'}
        if _project_is_selected: self.enabled_menu_ids.update(['menuitem_sounds'])
        if self.audio_is_available: self.enabled_menu_ids.update(['menuitem_words','menuitem_pictures','menuitem_render'])
        #Logging (only logs when project selected)
        try:
           logging.log(100,'"'+self.account_id+'","'+self.selected_project+'","'+self.request.uri+'"')
        except:
           pass

    def dbpost(self,url,data):
        headers = {
           "Authorization": "Bearer "+self.token,
           "Content-Type": "application/json"
                  }
        return requests.post(url, headers=headers, data=json.dumps(data))

    def get(self):
        #self.write("<h1><center>WORK IN PROGRESS<br>PLEASE DON'T USE AT THE MOMENT</center></h1>")
        self.write(self.template_header.generate())
        self.write(self.template_menu.generate(familar_name=self.familiar_name,
                                               enabled_menu_ids=self.enabled_menu_ids,
                                               helptext_html=self.helptext_html,
                                               contents_html=self.contents_html))

class SettingsHandler(MenuHandler):
    def getUsersProjects(self):
        userpath="userfiles/"+self.account_id+"/"
        s = sorted(glob.glob(userpath+"*"))
        f=[]
        for e in s:
           f.append(e[len(userpath):])
        return f

    def get(self):
        userprojects=self.getUsersProjects()
        self.enabled_menu_ids.discard('menuitem_settings')
        if len(userprojects)==0:
            self.helptext_html = self.loader.load("settings_help_no_projects.html").generate()
            self.set_cookie('show_tutorials','true')
        else:
            self.helptext_html = self.loader.load("settings_help.html").generate()
        self.contents_html = self.loader.load("settings.html").generate(projects=userprojects,
                                                               selected_project=self.selected_project)
        super(SettingsHandler, self).get()

class SoundsHandler(MenuHandler):
    def get(self):
        self.enabled_menu_ids.discard('menuitem_sounds')
        if not self.audio_is_available:
            self.helptext_html = self.loader.load("sounds_help_no_audio.html").generate()
        else:
            self.helptext_html = self.loader.load("sounds_help.html").generate()
        self.contents_html = self.loader.load("sounds.html").generate()
        super(SoundsHandler, self).get()

class WordsHandler(MenuHandler):
    def get(self):
        self.enabled_menu_ids.discard('menuitem_words')
        self.helptext_html = self.loader.load("words_help.html").generate()
        self.contents_html = self.loader.load("words.html").generate()
        super(WordsHandler, self).get()

class PicturesHandler(MenuHandler):
    def get(self):
        self.enabled_menu_ids.discard('menuitem_pictures')
        self.helptext_html = self.loader.load("pictures_help.html").generate()
        self.contents_html = self.loader.load("pictures.html").generate()
        super(PicturesHandler, self).get()

class RenderHandler(MenuHandler):
    def get(self):
        self.enabled_menu_ids.discard('menuitem_render')
        self.helptext_html = self.loader.load("render_help.html").generate()
        self.contents_html = self.loader.load("render.html").generate()
        super(RenderHandler, self).get()

class LogoutHandler(MenuHandler):
    def get(self):
        self.dbpost("https://api.dropboxapi.com/2/auth/token/revoke",None)
        self.clear_all_cookies()
        requests.get("https://www.dropbox.com/logout")
        self.redirect("/")

class InitUserHandler(MenuHandler):
    def get(self):
        user_path = "userfiles/"+self.account_id+"/"
        if not os.path.exists(user_path):
            os.makedirs(user_path, exist_ok=False)
        self.redirect("/")

class LogHandler(tornado.web.RequestHandler):
   def get(self):
        _account_id = tornado.escape.to_basestring(self.get_secure_cookie('account_id'))
        if not _account_id or (_account_id!=ADMIN1 and _account_id!=ADMIN2):
            self.send_error(404)
            return
        self.write("<PRE>")
        with open("logs/access.log", 'r') as f:
            self.write(f.read())

class DataHandler(tornado.web.RequestHandler):
   def initialize(self):
        self.account_id = tornado.escape.to_basestring(self.get_secure_cookie('account_id'))
        if not self.account_id: return #Allow no setup
        self.user_path = "userfiles/"+self.account_id+"/"
        self.selected_project = tornado.escape.to_basestring(self.get_cookie('selected_project'))
        if not self.selected_project: return #Allow partial setup
        self.project_path = self.user_path+self.selected_project+"/"
        self.project_filename = self.project_path+"DICHE.json"
        #logging.log(100,'"'+self.account_id+'","'+self.selected_project+'","'+self.request.method+'","'+self.request.uri+'"')

class InitProjectHandler(DataHandler):
    def get(self):
        os.makedirs(self.project_path, exist_ok=False)
        with open(self.project_filename, 'w') as f:
            init_project_object = {'showtuts':'true','account_id':self.account_id,'imagelist':[]}
            f.write(json.dumps(init_project_object))
            f.close()

class ProjectItemsHandler(DataHandler):
    def get(self):
        with open(self.project_filename, 'r+') as f:
            self.write(f.read())

    def post(self):
        with open(self.project_filename, 'bw') as f:
            f.write(self.get_argument("project_object"))

class ProjectItemHandler(DataHandler):
    def get(self):
        if not hasattr(self, 'project_filename'):
            self.write(json.dumps({'showtuts':'true'}))
            return
        with open(self.project_filename, 'r+') as f:
            text = f.read()
            o=json.loads(text)
            r={}
            for itemname in self.request.arguments:
                if itemname in o:
                   r[itemname]=o[itemname]
                else:
                   r[itemname]=None
            self.write(json.dumps(r))

    def put(self):
        with open(self.project_filename, 'r+') as f:
            text = f.read()
            o=json.loads(text)
            for itemname in self.request.arguments:
                itemvalue=tornado.escape.to_basestring(self.request.arguments[itemname][0])
                o[itemname]=itemvalue
            text=json.dumps(o)
            f.seek(0)
            f.write(text)
            f.truncate()

    def delete(self):
        with open(self.project_filename, 'r+') as f:
            text = f.read()
            o=json.loads(text)
            for itemname in self.request.arguments:
                if itemname in o:
                    del o[itemname]
            text=json.dumps(o)
            f.seek(0)
            f.write(text)
            f.truncate()

class SetAudioHandler(DataHandler):
    def post(self):
        audiofileurl = self.get_argument("fileurl")
        audiofilename = self.project_path+audiofileurl.split('/')[-1]
        with open(audiofilename, 'bw') as f:
            r = requests.get(audiofileurl)
            f.write(r.content)
        if audiofilename[-3:].lower()=='amr': #bug in ffmpeg for amr?
            params = ["sox",audiofilename,self.project_path+"DICHE.mp3"]
            subprocess.check_call(params)
        else:
            ff = ffmpy.FFmpeg(
                inputs={audiofilename: None},
                outputs={
                   self.project_path+"DICHE.mp3": '-loglevel fatal -y -acodec libmp3lame -ab 128k'
                } 
            )
            ff.run() #print(ff.run())
        os.remove(audiofilename)

class ImageSetHandler(DataHandler):
    def getKey(item):
        return item['imagetime']

    def post(self):
        def getKey(item):
            return float(item['imagetime'])
        #Download new image
        imagefileurl = self.get_argument("fileurl")
        srcimagefilename = self.project_path+self.get_argument("imagename")
        with open(srcimagefilename, 'bw') as f:
            r = requests.get(imagefileurl)
            f.write(r.content)
        #Convert to standard format and name
        newimagename=str(int(time.time()*1000))+str(random.randint(1000,9999))+".jpg"
        newimagefilename = self.project_path+newimagename
        params = ['convert',
                  '-resize','1280x720',
                  srcimagefilename,
                  '-background','black',
                  '-gravity','center',
                  '-extent','1280x720',
                  newimagefilename]
        subprocess.check_call(params)
        os.remove(srcimagefilename)
        #Add info to project
        imagetime = self.get_argument("imagetime")
        with open(self.project_filename, 'r+') as f:
            o=json.loads(f.read())
            o["imagelist"].append({"imagetime":imagetime,"imagename":newimagename})
            o["imagelist"].sort(key=getKey)
            f.seek(0)
            f.write(json.dumps(o))
            f.truncate()
        #Return new image name
        self.write(newimagename)

    def delete(self):
        imageindex = int(self.get_argument("index"))
        with open(self.project_filename, 'r+') as f:
            o=json.loads(f.read())
            #Delete existing image
            imagename = o["imagelist"][imageindex]['imagename']
            imagefilename = self.project_path+imagename
            if os.path.exists(imagefilename):
                os.remove(imagefilename)
            #Remove info from project
            o["imagelist"].remove(o["imagelist"][imageindex])
            f.seek(0)
            f.write(json.dumps(o))
            f.truncate()

class CreateImageHandler(DataHandler):
    def post(self):
        words = code=self.get_argument('words',default="")
        newimagefilename = self.project_path+"words.jpg"
        if("".join(words.split())==""):
           params = ['convert',
                     '-size','1280x720',
                     'xc:black',
                     newimagefilename]
        else:
           params = ['convert',
                     '-background','black',
                     '-fill','white',
                     '-size','854x480',
                     '-gravity','center',
                     '-font','DejaVu-Serif',
                     'caption:'+words,
                     '-extent','1280x720',
                     newimagefilename]
        subprocess.check_call(params)

class CreateVideoHandler(DataHandler):
    def get(self):
        def toFrame(time):
            return int(float(time)*25.0)
        with open(self.project_filename, 'r+') as f:
            o=json.loads(f.read())
        duration=toFrame(o["duration"])
        if duration==0:
           self.send_error()
           return
        _out=duration
        imagelist=[]
        for i in o["imagelist"][::-1]:
           _path = self.project_path+i["imagename"]
           _in = toFrame(i["imagetime"])
           imagelist.insert(0,{"path":_path, "in":_in, "out":_out})
           _out = int(_in)-1
        #Remove any images that are displayer for less than a frame
        newimagelist = []
        for i in imagelist:
           if(i["out"]-i["in"]>0):
              newimagelist.append(i)
        imagelist = newimagelist

        params = ["./melt_pid.sh",self.project_path,"-profile","atsc_720p_25"]

        if len(imagelist)==0:
           params += ["colour:black",
                      "in=0",
                      "out="+str(duration)]
        elif len(imagelist)==1:
           params += [imagelist[0]["path"],
                      "in=0",
                      "out="+str(duration)]
        else:
           params += [imagelist[0]["path"],
                      "in=0",
                      "out="+str(imagelist[0]["out"]+10)]
           for i in range(1, len(imagelist)): 
              params += [imagelist[i]["path"],
                         "in="+str(imagelist[i]["in"]-10),
                         "out="+str(imagelist[i]["out"]+10),
                         #"-filter","affine",'transition.geometry="0=0,0:110%x110%;100=-100,-100:125%x125%"',
                         "-mix","20",
                         "-mixer","luma"] 
        params += ["-audio-track",self.project_path+"DICHE.mp3",
                   "-consumer","avformat:"+self.project_path+".DICHE.mp4","properties=x264-medium"]
        subprocess.Popen(params)

    def delete(self):
        pidfile = self.project_path+".meltpid"
        if not os.path.exists(pidfile):
           return
        with open(pidfile, 'r') as f:
            pid=int(f.read())
        os.kill(pid, signal.SIGTERM)
        #os.remove(pidfile) #removed by melt wrapper
        while os.path.exists(pidfile):
           time.sleep(0.5)

class UserFilesCheckHandler(DataHandler):
    def get(self, path):
        o={'exists':os.path.exists(self.user_path+path)}
        self.write(json.dumps(o))        

class AuthHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect("https://www.dropbox.com/1/oauth2/authorize"+
                          "?client_id="+APP_KEY+
                          "&response_type=code"+
                          "&redirect_uri=https://diche-app.eu.org:8888/authcallback"+
                          "&state=none")

class AuthCallbackHandler(tornado.web.RequestHandler):
    def get(self):
        code=self.get_argument('code',default=None)
        if code==None:
            self.redirect("/")
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
            self.redirect("/")

class RobotsHandler(tornado.web.RequestHandler):
   def get(self):
      self.write("User-agent: *\r\nDisallow: /\r\n");

def make_app():
    return tornado.web.Application([
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path':'static', 'default_filename':'index.html'}),
        (r"/inituser", InitUserHandler),
        (r"/initproject", InitProjectHandler),
        (r"/projectitems", ProjectItemsHandler),
        (r"/projectitem", ProjectItemHandler),
        (r"/setaudio", SetAudioHandler),
        (r"/imageset", ImageSetHandler),
        (r"/createimage", CreateImageHandler),
        (r"/createvideo", CreateVideoHandler),
        (r"/auth", AuthHandler),
        (r"/settings", SettingsHandler),
        (r"/sounds", SoundsHandler),
        (r"/words", WordsHandler),
        (r"/pictures", PicturesHandler),
        (r"/userfiles-check/(.*)", UserFilesCheckHandler),
        (r"/userfiles/(.*)", tornado.web.StaticFileHandler, {'path':'userfiles'}),
        (r"/render", RenderHandler),
        (r"/logout", LogoutHandler),
        (r"/log", LogHandler),
        (r"/robots.txt", RobotsHandler),
        (r"/favicon.ico()", tornado.web.StaticFileHandler, {'path':'static/images/fav/favicon.ico'}),
        (r"/", LandingHandler),
    ],debug=False, cookie_secret=COOKIE_SECRET)

if __name__ == "__main__":
    logging.basicConfig(level=0, #100,
                        filename="logs/access.log",
                        format='%(asctime)s%(message)s',
                        datefmt='%m/%d/%Y,%H:%M:%S,')
    #tornado.options.parse_command_line()
    app=make_app()
    #app.listen(8080)
    https_server=tornado.httpserver.HTTPServer(app)
    https_server.bind(8080)
    https_server.start(8)
    tornado.ioloop.IOLoop.current().start()
