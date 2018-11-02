from flask import *
from flask import request, Response
import cv2
import numpy as np
from PIL import Image
from lib.camera import Camera
from lib.panarama import Panarama
import subprocess as sp
import os

application = Flask(__name__)
TEST = False

def start():
    cams = [{"tz": "ID", "url": 'https://cf-stream.coastalwatch.com/cw/' + os.environ.get('CAMNAME', 'bondicamera') + '.stream/chunklist.m3u8',
             "framerate": int(os.environ.get('FR', '20')), "videolength": os.environ.get('LENGTH', '00:06:00')}]

    cam = Camera(cams, test=TEST)
    cam.start = True
    for img in cam:
        if cam.start:
            height, width, _ = img.shape
            panarama = Panarama(img,height,width)
            cam.start = False
        else:
            panarama.stitch(img)

        # if no more states
        if not panarama.REQUIREDSTATESBEFORERESET:
            cam.resetnext = True

        # either display at constant framerate (if zero display last frame)
        if (cam.framerate > 0 and cam.f % cam.framerate == 0) or (cam.framerate == 0 and cam.resetnext):
            if TEST:
                img = cv2.imencode('.jpg', img)[1]
                frame = img.tostring()
                # yield (b'--frame\r\n'
                #       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            else:
                frame = np.flip(panarama.raw, axis=2)
                (h, w, _) = frame.shape
                im = Image.fromarray(frame)
                name = cams[0]['url'][:-22].split('/')[-1]
                dir = "/tmp/frame-" +  name + ".jpeg"
                #im = im.resize((w, h*2), Image.ANTIALIAS)
                im.save(dir, quality=100)
                sp.check_call('gsutil -m mv -a public-read ' + dir + ' gs://handy-contact-219622.appspot.com/frame-' + name + '.jpeg',shell=True)


@application.route('/')
def index():
   return Response(start(), mimetype='multipart/x-mixed-replace; bxoundary=frame')


if __name__ == "__main__":
    if TEST:
        application.run(debug=True, host='0.0.0.0', port=8000)
    else:
        start()

"""
gcloud container clusters create test-cluster \
--num-nodes 1 \
--scopes https://www.googleapis.com/auth/devstorage.full_control
"""