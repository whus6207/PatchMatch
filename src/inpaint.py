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
      ann, annd = getNNF()

# def inpaint(img, mask):
#   xs, ys = np.where(mask.border > 0)
#   scoreMap = mask.border.copy()
#   tarPosMap = {}
#   srcBlockMap = {}

#   # NNF(img, (xs, ys), 5)
#   for iteration in range(10):
#     for i in range(len(xs)):
#       if tarPosMap.has_key((xs[i], ys[i])):
#         OriScore = scoreMap[(xs[i], ys[i])]
#         # have value, update it
#         cpos = (xs[i], ys[i])
#         ctpos = tarPosMap[cpos]
#         csrcblock = srcBlockMap[cpos]
#         cscore = scoreMap[cpos]
#         # find nearby border for better score

#         if iteration %2 == 0:
#           offsets = [[-1, 0], [0, -1]]
#         else:
#           offsets = [[1, 0], [0, 1]]
#         for offset in offsets:
#           Pos1 = (cpos[0]+offset[0], cpos[1])
#           if scoreMap[Pos1[0], Pos1[1]] > 0:
#             tarPos1 = (tarPosMap[Pos1][0]-offset[0], tarPosMap[Pos1][1])
#             tarBlock1 = convert(getblock(img, tarPos1))
#             score1 = c2d(csrcblock, tarBlock1, mode='same').max()
#             if score1 > cscore:
#               cscore = scoreMap[xs[i], ys[i]] = score1
#               tarPosMap[cpos] = tarPos1

#         for x, y in [(cpos[0]-1, cpos[1]), (cpos[0], cpos[1]-1)]:
#           if scoreMap[x, y] > 0 and scoreMap[x, y] > cscore:
#             tmpPos = tarPosMap[(x, y)]
#             for l, k in getNearBy(tmpPos, size=3, limit=img.shape):
#               block = convert(getblock(img, (l, k)))
#               score = c2d(csrcblock, block, mode='same').max()
#               if score > cscore:
#                 cscore = scoreMap[xs[i], ys[i]] = score
#                 tarPosMap[(xs[i], ys[i])] = (l, k)
#         # update randomly 5 time
#         for time in range(5):
#           while True:
#             pos = (random.randint(0, img.shape[0]-1), random.randint(0, img.shape[1]-1))
#             if not mask.isMasked(pos):
#               break
#           tarBlock = convert(getblock(img, pos))
#           score = c2d(csrcblock, tarBlock, mode='same').max()
#           if score > cscore:
#             cscore = scoreMap[xs[i], ys[i]] = score
#             tarPosMap[(xs[i], ys[i])] = pos

#         if cscore != OriScore:
#           update += 1
#       else:
#         # random assign value
#         while True:
#           pos = (random.randint(0, img.shape[0]-1), random.randint(0, img.shape[1]-1))
#           if not mask.isMasked(pos):
#             break
#         srcblock = convert(getblock(img, (xs[i], ys[i])))
#         tarBlock = convert(getblock(img, pos))
#         score = c2d(srcblock, tarBlock, mode='same').max()

#         scoreMap[xs[i], ys[i]] = score
#         srcBlockMap[(xs[i], ys[i])] = srcblock
#         tarPosMap[(xs[i], ys[i])] = pos
      
#       # update the image
#       srcPos = (xs[i], ys[i])
#       tarPos = tarPosMap[srcPos]
#       tarBlock = getblock(img, tarPos, size=5)
#       for ii in range(tarBlock.shape[0]):
#         for jj in range(tarBlock.shape[1]):
#           l = (xs[i]-tarBlock.shape[0]/2+ii, ys[i]-tarBlock.shape[1]/2+jj)
#           if mask.isMasked(l):
#             img[l] = tarBlock[ii, jj]

#       # updating the frame
#       PlayerQueue.put(img.copy())

#     if iteration == 0:
#       print 'first finish'
#     else:
#       print 'second finish'
#   running.pop()
#   exit(1)


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