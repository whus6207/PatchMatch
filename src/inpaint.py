import numpy as np
import matplotlib.pyplot as npl
import matplotlib.cm as cm
import cv2
import Queue, threading, time
from scipy.ndimage import *
from header import *
from NNF_dll import *

patch_w = 13

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
    self.img = (1.*img[:, :, 0] + img[:, :, 1] + img[:, :, 2])/3
    self.img[self.img>=10] = 255
    self.img[self.img<10] = 0
    px, py = np.where(self.img > 0)
    self.bbox = [(px.min(), py.min()), (px.max(), py.max())]

  def shrink(self):
    self.img -= self.border
    self.img[self.img < 0] = 0


    px, py = np.where(self.img > 0)
    self.bbox = [(px.min(), py.min()), (px.max(), py.max())] if len(px) > 0 else [(None, None), (None, None)]

  def remains(self):
    n = (self.img > 0).sum()
    return n

  def isMasked(self, pos):
    x, y = pos
    return (self.img[x, y] != 0)

  def yeildOrder(self):
    self.border = self.img - binary_erosion(self.img).astype(self.img.dtype)*255

    blank = []
    xs, ys = np.where(self.border > 0)
    for (i, j) in zip(xs, ys):
      if self.isMasked((i, j)):
        block, upperleft = getblock(self.img, (i, j), size=patch_w)
        blank.append([(i,j), (block==0).sum()])
    blank = sorted(blank, key=lambda e: e[1], reverse=True)
    for i in blank:
      yield i[0]

def inpaint(img, mask, canvas = None, show=False):
  global patch_w

  PlayerQueue = Queue.Queue()
  running = [True]
  Player = App(PlayerQueue, running)
  Player.start()


  oriShape = img.shape
  setPatchW(patch_w)
  resize = 2
  img = cv2.resize(img[:, :, :3], (int(img.shape[1]/resize), int(img.shape[0]/resize)))
  mask = cv2.resize(mask[:, :, :3], (int(mask.shape[1]/resize), int(mask.shape[0]/resize)))
  mask = Mask(mask)

  img1 = img.copy()
  xs, ys = np.where(mask.img != 0)
  for x, y in zip(xs, ys):
    img1[x, y] = [0, 0, 0]
 
  while mask.remains() > 0:
    print 'remain mask', mask.remains()
    
    ul = [max(mask.bbox[0][0] - img.shape[0]/3, 0), max(mask.bbox[0][1] - img.shape[1]/3, 0)]
    br = [min(mask.bbox[1][0] + img.shape[0]/3, img.shape[0]), min(mask.bbox[1][1] + img.shape[1]/3, img.shape[1])]

    setMaskedArea(mask.img[ul[0]: br[0], ul[1]: br[1]])
    bitmap1 = np2Bitmap(img[ul[0]: br[0], ul[1]: br[1]])
    bitmap2 = np2Bitmap(img[ul[0]: br[0], ul[1]: br[1]])
    ann, annd = patchmatch(bitmap1, bitmap2)
    k = 0
    for index, (x, y) in enumerate(mask.yeildOrder()):
      pos = map(int, [ann[x-ul[0], y-ul[1]][0] + ul[0], ann[x-ul[0], y-ul[1]][1] + ul[1]])

      if show and np.random.rand(1)[0] > 0.9:
        k += 1
        showMatch((x, y), pos, img1, img, show=False, subplotIndex=(3,1,k))
        if k == 3:
          k = 0
          npl.subplots_adjust(left=0., right=1., top=1., bottom=0.0, wspace=0.02, hspace=0.)
          npl.show()
      
      img1[x, y] = img[pos[0], pos[1]]

      # if PlayerQueue is not None and index % 10 == 0:
      #   PlayerQueue.put(img1.copy())
    mask.shrink()

  while PlayerQueue.qsize() != 0 and running:
    time.sleep(0)
  running.pop()
  return cv2.resize(img1.copy(), (oriShape[1], oriShape[0]))


def main():
  origin = npl.imread('../image/seam_carving.jpg')
  mask = npl.imread('../image/seam_carving-mask.jpg')

  # origin = npl.imread('../image/example6.jpg')
  # mask = npl.imread('../image/example6-mask.jpg')
  print origin.shape
  start = time.time()
  final = inpaint(origin, mask)
  print 'use', time.time() - start, 'second'
  return

if __name__ == "__main__":
  main()

