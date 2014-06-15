import numpy as np
import matplotlib.pyplot as npl
import subprocess

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

def runNNF(fileA, fileB):
  subprocess.call("ANN.exe %s %s ann.raw annd.raw"%(fileA, fileB), shell=True)

def getNNF(annFile, anndFile):
  # subprocess.call("ANN.exe %s %s ann.raw annd.raw"%(fileA, fileB), shell=True)
  file = open(annFile, 'rb')
  ann = []
  while True:
    rgb = file.read(4)
    if len(rgb) != 4 or rgb == '':
      break
    else:
      rgb = map(ord, rgb)
    data = rgb[2]<<16 | rgb[1]<<8 | rgb[0]
    ann.append((data >> 12, data & 0x00000FFF))
  file.close()


  file = open(anndFile, 'rb')
  annd = []
  while True:
    rgb = file.read(4)
    if len(rgb) != 4 or rgb == '':
      break

    else:
      rgb = map(ord, rgb)
    data = rgb[2]<<16 | rgb[1]<<8 | rgb[0]
    annd.append(data)
  file.close()

  return np.array(ann), np.array(annd)
