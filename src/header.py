import numpy as np
import matplotlib.pyplot as npl
import time
from NNF_dll import *

def RGBtoGray(img):
  gray = np.dot(img[..., :3], [0.299, 0.587, 0.144])
  gray[gray > 255] = 255
  gray[gray <   0] = 0
  return gray.astype("uint8")
def GraytoRGB(img):
  if (len(img.shape) == 3 and img.shape[2] > 1):
    print 'only 1-channel grey scale image can be converted to RGB'
  colorImg = np.zeros((img.shape[0], img.shape[1], 3), dtype=img.dtype)
  colorImg[:, :, 0] = img
  colorImg[:, :, 1] = img
  colorImg[:, :, 2] = img
  return colorImg


def getblock(img, pos, size=7):
  block = img[max(pos[0]-size/2, 0): min(pos[0]+size/2+1, img.shape[0]), max(pos[1]-size/2, 0): min(pos[1]+size/2+1, img.shape[1])]
  return block, (pos[0]-size/2, pos[1]-size/2)

def markArea(img, pos, size=7, color=0x000000, width=1):
  img = img.copy()
  for i in range(pos[0], pos[0]+size):
    for j in range(pos[1], pos[1]+size):
      if i < pos[0]+width or j < pos[1]+width or i > pos[0]+size - 1 - width or j > pos[1]+size - 1 - width:
        img[i, j] = [color>>16 & 0xff, color >> 8 & 0xff, color & 0xff]
  return img

def paintLine(pos1, pos2, img, color=0xffffff):
  xs = range(pos1[0], pos2[0], 1 if pos2[0] > pos1[0] else -1)
  ys = range(pos1[1], pos2[1], 1 if pos2[1] > pos1[1] else -1)

  vector = [xs[-1]-xs[0] if len(xs) != 0 else 0, ys[-1]-ys[0] if len(ys) != 0 else 0]

  color = [color>>16 & 0xff, color >> 8 & 0xff, color & 0xff]
  if len(xs) < len(ys):
    for y in ys:
      img[pos1[0] + vector[0]*(y-pos1[1])/vector[1], y] = color
  else:
    for x in xs:
      img[x, pos1[1] + vector[1]*(x-pos1[0])/vector[0]] = color
  return img

def showMatch(pos1, pos2, img1, img2, subplotIndex=None, show=True):
  img1 = markArea(img1, (pos1[0]-7/2, pos1[1]-7/2), width = 2, color=0xff0000)
  img2 = markArea(img2, (pos2[0]-7/2, pos2[1]-7/2), width = 2, color=0xff0000)

  height = max(img1.shape[0], img2.shape[0])
  width = img1.shape[1] + img2.shape[1] + 10
  canvas = np.zeros((height, width, 3), dtype=img1.dtype)
  canvas[:img1.shape[0], :img1.shape[1]] = img1
  canvas[:img2.shape[0], img1.shape[1]+10:] = img2

  canvas = paintLine(pos1, (pos2[0], img1.shape[1]+10+pos2[1]), canvas, color=0x0000ff)

  if subplotIndex:
    npl.subplot(subplotIndex[0], subplotIndex[1], subplotIndex[2]).imshow(canvas)
    npl.axis('off')
  else:
    npl.imshow(canvas)
    npl.axis('off')

  if show:
    npl.show()

def reconstruct(img1, ann, img2, show=False):
  k = 0
  temp = np.zeros((ann.shape[0], ann.shape[1], img2.shape[2]), dtype=img2.dtype)
  for i in range(7, ann.shape[0]-7):
    for j in range(7, ann.shape[1]-7):
      pos = map(int, ann[i, j])
      temp[i, j] = img2[pos[0], pos[1]]

      if show and np.random.rand(1)[0] > 0.998:
        k += 1
        showMatch((i, j), pos, img1, img2, show=False, subplotIndex=(3,1,k))
        if k == 3:
          k = 0
          npl.subplots_adjust(left=0., right=1., top=1., bottom=0.0, wspace=0.02, hspace=0.)
          npl.show()
  return temp

if __name__ == "__main__":
  a = npl.imread('../image/seam_carving.jpg')
  b = npl.imread('../image/seam_carving.jpg')


  bitmap1 = np2Bitmap(a)
  bitmap2 = np2Bitmap(b)
  ann, annd = patchmatchc(bitmap1, bitmap2)
  reconstruct(a, ann, b, show=True)