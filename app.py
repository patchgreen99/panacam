from flask import *
from flask import request, Response
import cv2
import numpy as np
from PIL import Image
from lib.camera import Camera
from lib.panarama import Panarama
import subprocess as sp


application = Flask(__name__)
TEST = False

def start():
    cam = Camera(test=TEST)
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
                dir = "/tmp/frame.jpeg"
                im = im.resize((w, h*2), Image.ANTIALIAS)
                im.save(dir, quality=100)
                sp.check_call('gsutil -m mv -a public-read /tmp/frame.jpeg gs://handy-contact-219622.appspot.com/frame.jpeg',shell=True)


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