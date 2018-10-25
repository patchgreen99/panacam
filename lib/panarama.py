import cv2
import numpy as np


class Panarama:
    def __init__(self, img, height, width):
        self.dimensions = {"x1": 0, "x2": width, "y1": 0, "y2": height}
        self.raw = img
        self.dp = np.array([0, 0])
        self.maxfromtop = 0
        self.minfrombot = 9999999999999
        self.leftmostpoint = 0
        self.rightmostpoint = 0

        self.POS = 'LEFT_LAST'
        self.DIR = 'NONE'
        self.REQUIREDSTATESBEFORERESET = ['LEFT_LAST_GOING_RIGHT',
                                          'LEFT_LAST_NONE',
                                          'RIGHT_LAST_GOING_LEFT',
                                          'RIGHT_LAST_NONE',
                                          'NONE_GOING_RIGHT']

        self.nonpolar = self.lastnonpolar = self.parsenonpolar(img)


    def parsenonpolar(self, src):
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        return np.float32(src)


    def horizontal(src1, src2):
        p1 = cv2.phaseCorrelate(src1, src2)
        r = np.array(list(p1[0])).astype("int")
        return r, src2


    def stitch(self, img):
        self.lastnonpolar = self.nonpolar
        self.nonpolar = self.parsenonpolar(img)

        dp1, conv = self.horizontal(self.lastnonpolar, self.nonpolar)
        dp = np.array([dp1[0], dp1[1]])
        dp *= -1

        self.dp = np.array([0, 0])
        self.dp+=dp

        if self.dp[0] < 0:
            self.DIR = "GOING_LEFT"
        elif self.dp[0] > 0:
            self.DIR = "GOING_RIGHT"
        else:
            self.DIR = "NONE"

        height, width, _ = self.raw.shape
        # LEFT
        if self.dp[0] < 0 and self.dimensions["x1"] + self.dp[0] < 0:
            self.raw = np.hstack([np.ones((height,np.abs(self.dp[0]),3), dtype='uint8')*255, self.raw])

        # RIGHT
        elif self.dp[0] > 0 and self.dimensions["x2"] + self.dp[0] > width:
            self.raw = np.hstack([self.raw, np.ones((height, np.abs(self.dp[0]), 3), dtype='uint8')*255])
            self.DIR = "GOING_RIGHT"

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


        (h,w,_) =  self.raw[self.dimensions["y1"]:self.dimensions["y2"],self.dimensions["x1"]:self.dimensions["x2"]].shape
        (rawheight, rawwidth, _) = self.raw.shape

        tostream = np.vstack([np.ones((self.dimensions["y1"], w, 3), dtype='uint8')*255, img, np.ones((rawheight-self.dimensions["y2"] ,w , 3), dtype='uint8')*255])
        self.raw[:,self.dimensions["x1"]:self.dimensions["x2"]] = tostream

        (rawheight, rawwidth, _) = self.raw.shape
        self.maxfromtop = max(self.maxfromtop, self.dimensions["y1"])
        self.minfrombot = min(self.minfrombot, self.dimensions["y2"])


        # Just flatten bottom of image
        # if self.dimensions["y1"] > 0:
        #     self.raw[:self.maxfromtop] = np.ones((self.maxfromtop, rawwidth ,3), dtype='uint8')*255

        if self.dimensions["y2"] != rawheight:
            self.raw[self.minfrombot:] = np.ones((rawheight - self.minfrombot, rawwidth ,3), dtype='uint8')*255

        #print "{}_{}".format(self.POS, self.DIR), "STATES " + str(self.REQUIREDSTATESBEFORERESET)
        if self.REQUIREDSTATESBEFORERESET[-1] == "{}_{}".format(self.POS, self.DIR):
            self.REQUIREDSTATESBEFORERESET.pop()

        # set latest
        if 0 == self.dimensions["x1"]:
            self.POS = 'LEFT_LAST'
        elif rawwidth ==  self.dimensions["x2"]:
            self.POS = 'RIGHT_LAST'
        else:
            self.POS = 'NONE'

        # clean image
        #self.raw = self.raw[~np.all(np.sum(self.raw, axis=2) == 0, axis=1)]