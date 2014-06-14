import numpy as np
import matplotlib.pyplot as npl

def RGBtoGray(img):
  gray = np.dot(img[..., :3], [0.299, 0.587, 0.144])
  gray[gray > 255] = 255
  gray[gray <   0] = 0
  return gray.astype("uint8")
def GraytoRGB(img):
  if (len(img.shape) == 3 and img.shape[2] > 1):
    print 'only 1-channel grey scale image can be converted to RGB'
  colorImg = np.zeros((img.shape[0], img.shape[1], 3))
  colorImg[:, :, 0] = img
  colorImg[:, :, 1] = img
  colorImg[:, :, 2] = img
  return colorImg

# need reshape after return
def getNNF(filepath):
  file = read(filepath, 'rb')
  a = []
  while True:
    rgb = file.read(3)
    if rgb == '':
      break
    data = rgb[0]<<16 | rgb[1]<<8 | rgb[2]
    by = data >> 12 
    bx = data & 0x00000FFF
    a.append((by, bx))
  return np.array(a)