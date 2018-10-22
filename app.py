from flask import *
from flask import request, Response
import cv2
import numpy as np
from PIL import Image
from lib.camera import Camera
from lib.panarama import Panarama
import googleapiclient.discovery
import googleapiclient.http
import subprocess as sp


application = Flask(__name__)
TEST = False
BUCKET_NAME = 'handy-contact-219622'
storage = googleapiclient.discovery.build('storage', 'v1')

#
def upload(file_object):
    body = {
        'name': 'frame.jpeg',
    }
    req = storage.objects().insert(
        bucket=BUCKET_NAME, body=body,
        media_body=googleapiclient.http.MediaIoBaseUpload(
            file_object, 'image/jpeg'))
    resp = req.execute()
    return resp


def start():
    cam = Camera(test=TEST)
    start = True
    for img in cam:
        if start:
            height, width, _ = img.shape
            panarama = Panarama(img,height,width)
            start = False
        else:
            panarama.stitch(img)

        if TEST:
            frame = cv2.imencode('.jpg', panarama.raw)[1].tostring()
            # yield (b'--frame\r\n'
            #       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            if cam.f % 20 == 0:
                frame = np.flip(panarama.raw, axis=2)
                im = Image.fromarray(frame)
                dir = "/tmp/frame.jpeg"
                im.save(dir)
                sp.check_call('gsutil -m mv -a public-read /tmp/frame.jpeg gs://handy-contact-219622.appspot.com/frame.jpeg',shell=True)

        start = False

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