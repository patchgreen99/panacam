import subprocess as sp
import cv2
import numpy as np
import shlex
import requests
import re
from datetime import datetime, timedelta, time

OPENSSL_FFMPEG = 'ffmpeg' #'/home/charlotteg_mintz/ffmpeg/ffmpeg' # os.environ("OPENSSL_FFMPEG")
YOUTUBE_DL = 'youtube-dl' #'/usr/local/bin/youtube-dl'

CAMS = [
    {'tz': 'ID', 'url': 'https://cf-stream.coastalwatch.com/cw/bondicamera.stream/chunklist.m3u8', 'type': 'youtube-dl', 'name': u'Guethary - Parlementia', 'page': u'guethary---parlementia-france_49095'}
]

class Camera:
    def __init__(self, type=None, url=None, test=False):
        self.type = type
        self.url = url
        self.test = test
        self.framerate = 3
        self.totalframes = None
        self.f = -1
        self.cam = -1
        self.pipes = self._getpipes()
        self.name = self._getname()

    def _getwakezones(self):
        now = datetime.utcnow().time()
        TZ = {'UK': (time(6, 0, 0), time(18, 0, 0)),
                'USE': (time(12, 0, 0), time(0, 0, 0)),
                'ID': (time(22, 0, 0), time(13, 0, 0)),
                'USW': (time(15, 0, 0), time(3, 0, 0)),
                'HI': (time(16, 0, 0), time(8, 0, 0))}
        awake = []
        for tz, (dfrom, dto) in TZ.items():
            if dfrom > dto:
                if  dfrom <= now  or now <= dto:
                    awake.append(tz)
            elif dfrom <= dto:
                if dfrom <= now <= dto:
                    awake.append(tz)

        return awake

    def _getcams(self):
        out = []
        awakenow = self._getwakezones()
        for cam in CAMS:
            tz = cam.get('tz')
            if not tz or tz in awakenow:
                out.append(cam)
        return out

    def _geturl(self):
        cams = self._getcams()
        return cams[self.cam % len(cams)]['url']

    def _gettype(self):
        cams = self._getcams()
        return cams[self.cam % len(cams)]['type']

    def _getname(self):
        cams = self._getcams()
        state = re.search('([a-zA-Z]+)_[0-9]+$', cams[self.cam % len(cams)]['page'], flags=re.S).group(1)
        return cams[self.cam % len(cams)]['name'] + ', ' + state[:1].upper() + state[1:].lower()

    def _getcmds(self):
        type = self._gettype()
        url = self._geturl()
        self.name = self._getname()

        commands = {
            "youtube-dl": [(False, "{youtube_dl} " + url + " -o - "), (False, "{openssl_ffmpeg} -i - -q:v 0 -f image2pipe -")],

            "ffmpeg": [(False, "{openssl_ffmpeg} -i " + url + " -f image2pipe -q:v 1 -")],

            "livestreamer": [(False, "livestreamer " + url + " best -o - "), (False, "{openssl_ffmpeg} -i - -q:v 0 -f image2pipe -")],

            #"ipcam": [(False, "youtube-dl -f '[height<=360]' http://s10.ipcamlive.com/streams/" + self._getipcamlive(url) + "/playlist.m3u8  -o - "), (False, "{openssl_ffmpeg} -i - -q:v 0 -f image2pipe -")]
        }

        if self.test:
            #return [(True, "for a in /Users/patrick.green/wr_backend/tests/data/frames/*.jpg; do cat $a; done"), (False, "ffmpeg -i - -q:v 0 -f image2pipe -")]
            return [(False, "ffmpeg -i /Users/patrickgreen/panacam/testbali.mp4 -q:v 0 -f image2pipe -")]
        else:
            return [(s,r.format(openssl_ffmpeg=OPENSSL_FFMPEG, youtube_dl=YOUTUBE_DL)) for s,r in commands[type]]

    def _getpipes(self):
        # switch to the next cam every time this is called
        self.cam+=1
        currentpipe = None
        pipes = []
        for (shell, cmd) in self._getcmds():
            print cmd
            if not shell:
                cmd = shlex.split(cmd)

            if currentpipe is None:
                currentpipe = sp.Popen(cmd, stdout=sp.PIPE, bufsize=10 ** 8, shell=shell)
            else:
                newpipe = sp.Popen(cmd, stdout=sp.PIPE, stdin=currentpipe.stdout, bufsize=10 ** 8, shell=shell)
                currentpipe = newpipe
            pipes.append(currentpipe)
        return pipes

    def _getipcamlive(self, url):
        response1 = requests.get(url)
        for alias in re.findall('http:\/\/g0\.ipcamlive\.com\/player\/player\.php\?alias=(.*?)"', response1.content, flags=re.S):
            response2 = requests.get("http://g0.ipcamlive.com/player/player.php?alias=" + str(alias))
            for streamid in re.findall("var streamid ?= ?'(.*?)';", response2.content, flags=re.S):
                return str(streamid)
        return ''

    def _doreset(self):
        # reset frames
        self.f = 0
        # kill previous pipes
        for pipe in self.pipes:
            try:
                pipe.kill()
            except:
                # can't kill because dead
                pass
        # Returns next stream
        self.pipes = self._getpipes()

    def __iter__(self):
        bytes = ''
        while True:
            # Camera Expiry
            # if self.totalframes and self.f > self.totalframes:
            #     self._doreset()
            #
            # if self.pipes[0].poll() is not None:
            #     self._doreset()

            bytes += self.pipes[-1].stdout.read(1024)

            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes[a:b + 2]
                bytes = bytes[b + 2:]

                # cut out some frames
                self.f += 1
                if self.f % self.framerate == 0:
                    img = np.fromstring(jpg, dtype=np.uint8)
                    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
                    img = np.array(img)
                    yield img