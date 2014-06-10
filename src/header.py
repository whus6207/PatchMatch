import numpy as np
import matplotlib.pyplot as npl


def RGBtoGray(img):
  return np.dot(img[..., :3], [0.299, 0.587, 0.144])
def GraytoRGB(img):
  if (len(img.shape) == 3 and img.shape[2] > 1):
    print 'only 1-channel grey scale image can be converted to RGB'
  colorImg = np.zeros((img.shape[0], img.shape[1], 3))
  colorImg[:, :, 0] = img
  colorImg[:, :, 1] = img
  colorImg[:, :, 2] = img
  return colorImg