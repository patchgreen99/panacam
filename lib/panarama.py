import cv2
from scipy.misc import imread, imresize
from lib.features import *


class Panarama:
    def __init__(self, img, height, width):
        self.dimensions = {"x1": 0, "x2": width, "y1": 0, "y2": height}
        self.raw = img
        self.dp = np.array([0, 0])
        self.dr = np.array([0, 0])
        self.zoomlevel = 0
        self.lastzooms = []

        self.nonpolar = self.lastnonpolar = img
        self.polar = self.lastpolar = self.parsepolar(img)


    def parsepolar(self, img):
        height, width, _ = img.shape
        middle = (height / 2, width / 2)
        polar, r_i, theta_i = reproject_image_into_polar(img, middle)
        polar = cv2.cvtColor(polar, cv2.COLOR_BGR2GRAY)
        #polar = np.mod(np.sum(polar, axis=2), 255).astype(int)
        #polar = cv2.adaptiveThreshold(polar, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return polar[:,:180]


    def stitch(self, img):
        self.lastpolar = self.polar
        self.lastnonpolar = self.nonpolar

        self.nonpolar = img
        self.polar = self.parsepolar(img)

        dr, convPolar = zoom(self.lastpolar, self.polar)
        dp1, conv = horizontal(self.lastnonpolar, self.nonpolar)
        dp2, conv1 = vertical(self.lastnonpolar, self.nonpolar)
        dp = np.array([dp1[0], dp2[1]])
        dp *= -1

        self.dr = np.array([0, 0])
        self.dp = np.array([0, 0])

        self.dr+=dr
        self.dr*=-1
        self.dp+=dp

        # # Zoom canvas
        # zoom in is negative
        # zoom out is positive
        self.zoomlevel += dr[1]
        self.lastzooms.append(dr[1])
        print self.zoomlevel, sum(self.lastzooms)/len(self.lastzooms)

        height, width, _ = self.raw.shape
        if dr[1] < 0:
            shift = int(np.sqrt(2) * dr[1] * -1 / 2.0)
            print shift
            # zoom in is negative
            # height, width, _ = self.raw.shape
            # newheight = height + shift * 2
            # newwidth = width + shift * 2
            # self.raw = imresize(self.raw, (newheight, newwidth))

            self.dimensions["x1"] = max(self.dimensions["x1"] + shift, 0)
            self.dimensions["x2"] = min(self.dimensions["x2"] - shift, width)
            self.dimensions["y1"] = max(self.dimensions["y1"] + shift, 0)
            self.dimensions["y2"] = min(self.dimensions["y2"] - shift, height)
            (h, w, _) = self.raw[self.dimensions["y1"]:self.dimensions["y2"], self.dimensions["x1"]:self.dimensions["x2"]].shape
            print (h, w, _)
            img = imresize(img, (h, w))


        elif dr[1] > 0:
            shift = int(np.sqrt(2) * dr[1] / 2.0)
            print shift
            # zoom out is positive
            # height, width, _ = self.raw.shape
            # newheight = height - shift * 2
            # newwidth = width - shift * 2
            # self.raw = imresize(self.raw, (newheight, newwidth))

            self.dimensions["x1"] = max(self.dimensions["x1"] - shift, 0)
            self.dimensions["x2"] = min(self.dimensions["x2"] + shift, width)
            self.dimensions["y1"] = max(self.dimensions["y1"] - shift, 0)
            self.dimensions["y2"] = min(self.dimensions["y2"] + shift, height)
            (h, w, _) = self.raw[self.dimensions["y1"]:self.dimensions["y2"], self.dimensions["x1"]:self.dimensions["x2"]].shape
            print (h, w, _)
            img = imresize(img, (h, w))



        height, width, _ = self.raw.shape
        # LEFT
        if self.dp[0] < 0 and self.dimensions["x1"] + self.dp[0] < 0:
            self.raw = np.hstack([np.ones((height,np.abs(self.dp[0]),3), dtype='uint8')*255,self.raw])
        # RIGHT
        elif self.dp[0] > 0 and self.dimensions["x2"] + self.dp[0] > width:
            self.raw = np.hstack([self.raw, np.ones((height, np.abs(self.dp[0]), 3), dtype='uint8')*255])
            self.dimensions["x1"] = self.dimensions["x1"] + self.dp[0]
            self.dimensions["x2"] = self.dimensions["x2"] + self.dp[0]
        else:
            self.dimensions["x1"] = self.dimensions["x1"] + self.dp[0]
            self.dimensions["x2"] = self.dimensions["x2"] + self.dp[0]


        height, width, _ = self.raw.shape
        # UP
        if self.dp[1] < 0 and self.dimensions['y1'] + self.dp[1] < 0:
            self.raw = np.vstack([np.ones((np.abs(self.dp[1]),width,3), dtype='uint8')*255, self.raw])
        # DOWN
        elif self.dp[1] > 0 and self.dimensions['y2'] + self.dp[1] > height:
            self.raw = np.vstack([self.raw, np.ones((np.abs(self.dp[1]), width, 3), dtype='uint8')*255])
            self.dimensions["y1"] = self.dimensions["y1"] + self.dp[1]
            self.dimensions["y2"] = self.dimensions["y2"] + self.dp[1]
        else:
            self.dimensions["y1"] = self.dimensions["y1"] + self.dp[1]
            self.dimensions["y2"] = self.dimensions["y2"] + self.dp[1]



        #print self.dimensions["y1"],self.dimensions["y2"],self.dimensions["x1"],self.dimensions["x2"]
        (h,w,_) =  self.raw[self.dimensions["y1"]:self.dimensions["y2"],self.dimensions["x1"]:self.dimensions["x2"]].shape
        (rawheight, rawwidth, _) = self.raw.shape
        #print (h,w,_)
        img = imresize(img, (h, w))

        tostream = np.vstack([np.ones((self.dimensions["y1"], w, 3), dtype='uint8')*255, img, np.ones((rawheight-self.dimensions["y2"] ,w , 3), dtype='uint8')*255])
        self.raw[:,self.dimensions["x1"]:self.dimensions["x2"]] = tostream

        # clean image
        #self.raw = self.raw[~np.all(np.sum(self.raw, axis=2) == 0, axis=1)]