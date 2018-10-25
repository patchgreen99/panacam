import subprocess as sp
import cv2
import numpy as np
from datetime import datetime, time
import json

OPENSSL_FFMPEG = 'ffmpeg'
YOUTUBE_DL = 'youtube-dl'


class Camera:
    def __init__(self, type=None, url=None, test=False):
        self.type = type
        self.url = url
        self.test = test
        self.f = -1
        self.cam = -1
        self.resetnext = False

        # reread json
        self.CAMS = self._getjsoncams()

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


    def _getjsoncams(self):
        if self.test:
            result = [{"tz": "ID", "url": "https://cf-stream.coastalwatch.com/cw/bondicamera.stream/chunklist.m3u8", "framerate": 1,  "videolength": "00:05:00"}]
        else:
            sp.check_call('gsutil cp gs://handy-contact-219622.appspot.com/cams.json /tmp/cams.json', shell=True)
            result = json.load(file('/tmp/cams.json'))

        out = []
        awakenow = self._getwakezones()
        for cam in result:
            tz = cam.get('tz')
            if not tz or tz in awakenow:
                out.append(cam)

        return out


    def _savevid(self):
        self.framerate = self.CAMS[0]["framerate"]
        self.resetnext = False
        self.start = True
        sp.check_call(
            "{openssl_ffmpeg} -i $({youtube_dl} --get-url ".format(openssl_ffmpeg=OPENSSL_FFMPEG, youtube_dl=YOUTUBE_DL) + self.CAMS[0]["url"] + ") -ss 00:00:00 -t " + self.CAMS[0]["videolength"] + " -q:v 0 -c:v copy -y -c:a copy /tmp/out.mp4", shell=True)


    def __iter__(self):
        self._savevid()
        #path = '/tmp/testbali.mp4' if self.test else '/tmp/out.mp4'
        path = '/tmp/out.mp4'
        vidcap = cv2.VideoCapture(path)
        success, image = vidcap.read()


        while True:
            if self.resetnext or not success:
                # grab new cams file
                if any(x != y for x, y in zip(self._getjsoncams(), self.CAMS)):
                    self.CAMS = self._getjsoncams()
                else:
                    # move round to next cam
                    self.CAMS.append(self.CAMS.pop())

                self._savevid()
                vidcap = cv2.VideoCapture('/tmp/out.mp4')
                success, image = vidcap.read()

            yield np.array(image)
            success, image = vidcap.read()
            self.f +=1