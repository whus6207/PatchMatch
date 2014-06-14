import numpy as np
import matplotlib.pyplot as npl
import cv2
import Queue, threading, time
from scipy.ndimage import *
from header import *
from scipy.signal import correlate2d  as c2d


import random
import sys
sys.setrecursionlimit(10000)

baseline = None

class App(threading.Thread):
  def __init__(self, queue, running):
    threading.Thread.__init__(self)
    self.queue = queue
    self.running = running

  def run(self):
    while self.running:
      try:
        self.img = self.queue.get(block=False)
      except Queue.Empty:
        pass
      except Exception, e:
        print e
        exit(1)
      else:
        self.changeImg()
      time.sleep(0)
  def changeImg(self):
    cv2.imshow('frame', self.img)
    if (cv2.waitKey(1) & 0xFF) == ord('q'):
      self.running.pop()

PlayerQueue = Queue.Queue()
running = [True]
Player = App(PlayerQueue, running)
Player.start()


class Mask:
  def __init__(self, img):
    self.img = RGBtoGray(img)
    self.img[self.img>=126] = 255
    self.img[self.img<126] = 0

    self.border = laplace(self.img);
    # self.component, self.componentN = label(self.img, generate_binary_structure(2,2))
    # self.component = (self.component).astype('uint8')

  def isMasked(self, pos):
    x, y = pos
    return (self.img[x, y] != 0)
  def mask(self, img):
    for i in range(img.shape[0]):
      for j in range(img.shape[1]):
        if self.isMasked((i, j)):
          img[i, j] = np.zeros(3)
    return img
  def showImg(self):
    cv2.imshow('mask-image', self.img)
    cv2.waitKey(0)

def getNearBy(pos, size=3, limit=(None, None)):
  r = range(-(size/2), size/2+1, 1)
  for i in r:
    for j in r:
      x = pos[0]+i if pos[0]+i >= 0 else -(pos[0]+i)
      y = pos[1]+j if pos[1]+j >= 0 else -(pos[1]+j)
      if limit[0] and x >= limit[0]:
        x = 2*limit[0] - x - 1
      if limit[1] and y >= limit[1]:
        y = 2*limit[1] - y - 1
      yield (x, y)        

def inpaint(img, mask):
  while mask.remains() > 0:
    xs, ys = np.where(mask.getBorder() > 0)
    for i in range(len(xs)):
      srcBlock = getblock(img, (xs[i], ys[i]))
      npl.imsave('block.jpg', srcBlock)

      ann, annd = getNNF('block.jpg', img.path)
      ann.reshape((srcBlock.shape[0], srcBlock.shape[1], 2))

      for ii in range(srcBlock.shape[0]):
        for jj in range(srcBlock.shape[1]):
          l = (xs[i]-srcBlock.shape[0]/2+ii, ys[i]-srcBlock.shape[1]/2+jj)
          if mask.isMasked(l):
            img[l[0], l[1]] = img[ann[ii, jj, 0], ann[ii, jj, 1]]
      mask.shrink()

def getblock(img, pos, size=11):
  global baseline
  # block = np.zeros((size*size, 3))
  # for index, (x, y) in enumerate(getNearBy(pos, size, limit=img.shape)):
  #   block[index] = img[x, y]
  # block = block.reshape((size, size, 3))

  block = img[pos[0]-size/2: pos[0]+size/2+1, pos[1]-size/2: pos[1]+size/2+1, 0:3]
  if baseline == None: 
    b = convert(block)
    baseline = c2d(b, b, mode='same').max()
  return block

def convert(block):
  block = block.dot([0.299, 0.587, 0.114])
  # import matplotlib.cm as cm
  # npl.imshow(block, cmap=cm.Greys_r)
  # npl.show()
  block = (block - block.mean())/block.std()
  return block

# origin = npl.imread('../image/example.jpg')[::2, ::2]
# mask = Mask(npl.imread('../image/example-mask.jpg')[::2, ::2])


# vacantImg = mask.mask(origin)
# inpaint(vacantImg, mask)
# running.pop()