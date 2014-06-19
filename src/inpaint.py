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
    self.img[self.img>=126] = 255
    self.img[self.img<126] = 0

  def shrink(self):
    # erase mask with the border
    self.img -= self.border

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


patch_w = 7
def inpaint(img, mask):
  global patch_w
  img1 = img.copy()
  img2 = img.copy()
  patch_w = setPatchW(patch_w)
  xs, ys = np.where(mask.img != 0)
  for x, y in zip(xs, ys):
    img1[x, y] = [0, 0, 0]
    img2[x, y] = [255, 255, 255]

  # bitmap2 = np2Bitmap(img2)
  # bitmap1 = np2Bitmap(img1)
  # ann, annd = patchmatch(bitmap1, bitmap2)
  # temp = np.zeros((ann.shape[0], ann.shape[1], 3), dtype=img1.dtype)
  # for i in range(ann.shape[0]):
  #   for j in range(ann.shape[1]):
  #     temp[i, j] = img2[ann[i,j,0], ann[i,j,1] ]
  # npl.imshow(temp)
  # npl.show()
  while mask.remains() > 0:
    print 'remain mask', mask.remains()
    border = mask.getBorder().copy()
    xs, ys = np.where(border > 0)

    # bitmap1 = np2Bitmap(img1)
    # bitmap2 = np2Bitmap(img2)

    fix = [(0, 0), (0, -1), (-1, -1), (-1, 0)]
    for x, y in zip(xs, ys):
      if border[x, y] != 0:
        srcBlock = getblock(img1, (x, y))
        dstBlock = getblock(img2, (x, y))

        diff = (1.*srcBlock - dstBlock)**2
        valueDiff1 = diff[:diff.shape[0]/2, :diff.shape[1]/2].sum() # upperleft
        valueDiff2 = diff[diff.shape[0]/2:diff.shape[0], :diff.shape[1]/2].sum() #bottomleft
        valueDiff3 = diff[:diff.shape[0]/2, diff.shape[1]/2:diff.shape[1]].sum() #upperright
        valueDiff4 = diff[diff.shape[0]/2:diff.shape[0], diff.shape[1]/2:diff.shape[1]].sum() #bottomright
        diff = [valueDiff1, valueDiff3, valueDiff4, valueDiff2]

        rot = diff.index(max(diff))        
        

        bitmap1 = np2Bitmap(srcBlock)
        bitmap2 = np2Bitmap(img2)
        ann, annd = patchmatch(bitmap1, bitmap2, rot, False)
        anncenter = ann[ann.shape[0]/2, ann.shape[1]/2]
        # value = img2[ann[rot][x, y, 0]+fix[rot][0], ann[rot][x, y, 1] + fix[rot][1]]
        value = img2[anncenter[0]+fix[rot][0], anncenter[1]+fix[rot][1]]
        img1[x, y] = value
        img2[x, y] = value

        # PlayerQueue.put(cv2.resize(img1.copy(), (img.shape[1]*3, img.shape[0]*3)))
    mask.shrink()
  return img1

def getblock(img, pos, size=25, patch_w=14):
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

origin = npl.imread('../image/example.jpg')[::2, ::2][::2, ::2]
mask = Mask(npl.imread('../image/example-mask.jpg')[::2, ::2][::2, ::2])


src = npl.imread('../image/railroad3.jpg')[::2, ::2]
target = npl.imread('../image/railroad2.jpg')[::2, ::2]

bit1 = np2Bitmap(src)
bit2 = np2Bitmap(target)
ann, annd = patchmatch(bit1, bit2)
npl.subplot(1, 3, 1).imshow(src)
npl.subplot(1, 3, 2).imshow(target)
npl.subplot(1, 3, 3).imshow(reconstruct(ann, target))
npl.show()
exit(1)
# origin = npl.imread('../image/example.jpg')[::2, ::2]
# mask = Mask(npl.imread('../image/example-mask.jpg')[::2, ::2])

# PlayerQueue = Queue.Queue()
# running = [True]
# Player = App(PlayerQueue, running)
# Player.start()


start = time.time()
img = inpaint(origin, mask)
print 'use', time.time() - start, 'second'
# while PlayerQueue.qsize() != 0:
#   time.sleep(0)
# running.pop()
npl.subplot(1,1,1).imshow(img)
npl.show()
