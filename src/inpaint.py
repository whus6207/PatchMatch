import numpy as np
import matplotlib.pyplot as npl
import matplotlib.cm as cm
import cv2
import Queue, threading, time
from scipy.ndimage import *
from header import *
from NNF_dll import *

import sys
sys.setrecursionlimit(10000)

class App(threading.Thread):
  def __init__(self, queue, running):
    threading.Thread.__init__(self)
    self.queue = queue
    self.running = running

  def run(self):
    while self.running:
      try:
        self.img = self.queue.get(block=False)
        if self.img == None:
          print pop()
          self.running.pop()
      except Queue.Empty:
        pass
      else:
        self.changeImg()
      time.sleep(0)
  def changeImg(self):
    self.img[:, :, [0, 2]] = self.img[:, :, [2, 0]]
    cv2.imshow('frame', self.img)
    if (cv2.waitKey(1) & 0xFF) == ord('q'):
      self.running.pop()




class Mask:
  def __init__(self, img):
    self.img = RGBtoGray(img)
    self.img = self.img.astype('float32')
    self.img[self.img>=10] = 255
    self.img[self.img<10] = 0

  def shrink(self):
    # erase mask with the border
    self.img -= self.border
    self.img[self.img < 0] = 0

  def remains(self):
    n = (self.img > 0).sum()
    return n

  def getBorder(self):
    self.border = self.img - binary_erosion(self.img).astype(self.img.dtype)*255
    # remove pixels that not in mask
    xs, ys = np.where(self.border > 0)
    a = 0
    for x, y in zip(xs, ys):
      if not self.isMasked((x, y)):
        self.border[x, y] = 0
        a += 1
    if a != 0:
      print 'unmasked area', a
    return self.border

  def isMasked(self, pos):
    x, y = pos
    return (self.img[x, y] != 0)

  def mask(self, img):
    img = img.copy()
    for i in range(img.shape[0]):
      for j in range(img.shape[1]):
        if self.isMasked((i, j)):
          img[i, j] = np.zeros(3)
    return img
  def showImg(self):
    a = self.img.copy()
    a[:, :, [0, 2]] = a[:, :, [2, 0]]
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



def inpaint(img, mask, canvas = None):
  oriShape = img.shape
  print img
  setPatchW(7)
  resize = 2
  img = img[:, :, :3]
  mask = mask[:, :, :3]

  img = cv2.resize(img, (int(img.shape[1]/resize), int(img.shape[0]/resize)))
  mask = cv2.resize(mask, (int(mask.shape[1]/resize), int(mask.shape[0]/resize)))
  mask = Mask(mask)

  img1 = img.copy()
  img2 = img.copy()
  xs, ys = np.where(mask.img != 0)
  for x, y in zip(xs, ys):
    img1[x, y] = [0, 0, 0]
    img2[x, y] = [255, 255, 255]
  while mask.remains() > 0:
    print 'remain mask', mask.remains()
    border = mask.getBorder().copy()
    xs, ys = np.where(border > 0)

    fix = [(0, 0), (0, -1), (-1, -1), (-1, 0)]
    order = zip(xs, ys)
    np.random.shuffle(order)
    for x, y in order:
      if border[x, y] != 0:
        srcBlock = getblock(img1, (x, y))
        dstBlock = getblock(img2, (x, y))

        diff = (1.*srcBlock - dstBlock)**2

        valueDiff1 = diff[:diff.shape[0]/2, :diff.shape[1]/2] # upperleft
        valueDiff2 = diff[diff.shape[0]/2:diff.shape[0], :diff.shape[1]/2] #bottomleft
        valueDiff3 = diff[:diff.shape[0]/2, diff.shape[1]/2:diff.shape[1]] #upperright
        valueDiff4 = diff[diff.shape[0]/2:diff.shape[0], diff.shape[1]/2:diff.shape[1]] #bottomright

        valueDiff1 = valueDiff1.mean()
        valueDiff2 = valueDiff2.mean()
        valueDiff3 = valueDiff3.mean()
        valueDiff4 = valueDiff4.mean()
        diff = [valueDiff1, valueDiff3, valueDiff4, valueDiff2]

        rot = diff.index(max(diff))

        bitmap1 = np2Bitmap(srcBlock)
        bitmap2 = np2Bitmap(img2)
        ann, annd = patchmatch(bitmap1, bitmap2, rot, False)

        color = [[255, 255, 255], [255, 0, 0], [0, 255, 0], [0, 0, 255]]
        for k in range(x, x+2):
          for q in range(y, y+2):
            if mask.isMasked((k,q)):
              annposition = ann[ann.shape[0]/2 + k-x + fix[rot][0], ann.shape[1]/2 + q-y + fix[rot][1]]
              value = img2[annposition[0], annposition[1]]
              # if the target place is not maseked
              if not mask.isMasked(annposition):
                img1[k, q] = value
                img2[k, q] = value

                mask.img[k, q] = 0
                border[k, q] = 0
              else:
                # find neareast unmasked pixel
                # print annposition, value, (k, q)
                value = []
                for kk in range(4):
                  for qq in range(4):
                    if not mask.isMasked((annposition[0] + kk-1, annposition[1] + qq-1)):
                      value.append(img1[annposition[0] + kk-1, annposition[1] + qq-1])

                value = reduce(lambda a,b: a+b, value)/len(value) if len(value) != 0 else [0, 0, 0]
                img1[k, q] = value
                img2[k, q] = value

        if canvas is not None:
          canvas.srcUpdate(cv2.resize(img1.copy(), (oriShape[1], oriShape[0])))       

        # PlayerQueue.put(cv2.resize(img1.copy(), (oriShape[1], oriShape[0])))
    mask.shrink()
  return cv2.resize(img1.copy(), (oriShape[1], oriShape[0]))

def getblock(img, pos, size=11, patch_w=11):
  size += patch_w
  block = img[pos[0]-size/2: pos[0]+size/2+1, pos[1]-size/2: pos[1]+size/2+1, 0:3]
  return block

def convert(block):
  block = block.dot([0.299, 0.587, 0.114])
  block = (block - block.mean())/block.std()
  return block

def reconstruct(ann, targetImage):
  temp = np.zeros((ann.shape[0], ann.shape[1], targetImage.shape[2]), dtype=targetImage.dtype)
  for i in range(ann.shape[0]):
    for j in range(ann.shape[1]):
      temp[i, j] = targetImage[ann[i, j, 0], ann[i, j, 1]]
  return temp

# PlayerQueue = Queue.Queue()
# running = [True]
# Player = App(PlayerQueue, running)
# Player.start()

# origin = npl.imread('../image/example.jpg')
# mask = npl.imread('../image/example-mask.jpg')

# start = time.time()
# img = inpaint(origin, mask)
# print 'use', time.time() - start, 'second'

# # while PlayerQueue.qsize() != 0 and running:
# #   time.sleep(0)
# # running.pop()
# npl.subplot(1,1,1).imshow(img)
# npl.show()
