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
        if self.img == 'exit':
          self.running.pop()
          break
      except Queue.Empty:
        pass
      else:
        self.changeImg()
      time.sleep(0.5)
  def changeImg(self):
    cv2.imshow('frame', swap2cv2(self.img))
    if (cv2.waitKey(1) & 0xFF) == ord('q'):
      self.running.pop()

PlayerQueue = Queue.Queue()
running = [True]
Player = App(PlayerQueue, running)
Player.start()


def swap2cv2(img):
  img = img.copy()
  t = img[:, :, 0].copy()
  img[:, :, 0] = img[:, :, 2].copy()
  img[:, :, 2] = t.copy()
  return img

class Mask:
  def __init__(self, img):
    self.img = RGBtoGray(img)
    self.img[self.img>=126] = 255
    self.img[self.img<126] = 0

    self.border = sobel(self.img) * 255
    self.oriimg = self.img.copy()

    self.shrink()

  def shrink(self):
    xs, ys = np.where(self.border > 0)
    for index, (x, y) in enumerate(zip(xs, ys)):
      # update the border
      self.border[x, y] = 0
      if self.isMasked((x, y)):
        self.img[x, y] = 0

      for xx, yy in getNearBy((x,y)):
        if self.isMasked((xx, yy)):
          self.border[xx, yy] = 255
          break
    # PlayerQueue.put(self.img.copy())
  def remains(self):
    n = (self.img > 0).sum()
    print n
    return n
  def getBorder(self):
    return self.border.copy()
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
    cv2.imshow('mask-image', swap2cv2(self.img))
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

def inpaint(imgPath, img, mask):
  while mask.remains() > 0:
    xs, ys = np.where(mask.getBorder() > 0)
    for x, y in zip(xs, ys):
      srcBlock = getblock(img, (x, y))
      npl.imsave('block.jpg', srcBlock)

      runNNF('block.jpg', imgPath)
      ann, annd = getNNF('ann.raw', 'annd.raw')
      ann = ann.reshape((srcBlock.shape[0], srcBlock.shape[1], 2))

      img[x, y] = img[ann[ann.shape[0]/2, ann.shape[0]/2, 0], ann[ann.shape[0]/2, ann.shape[0]/2, 1]]
      PlayerQueue.put(img.copy())
    mask.shrink()


def getblock(img, pos, size=25):
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

origin = npl.imread('../image/example.jpg')
origin2 = cv2.imread('../image/example.jpg')
mask = Mask(npl.imread('../image/example-mask.jpg'))
# while mask.remains() > 0:
  # mask.shrink()
# PlayerQueue.put('exit')

vacantImg = mask.mask(origin)
inpaint('../image/example.jpg', vacantImg, mask)
# running.pop()