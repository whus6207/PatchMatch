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

<<<<<<< HEAD
# need reshape after return
def getANN(filepath):
  file = read(filepath, 'rb')
  a = []
=======
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
>>>>>>> a0ce5d9b48285ce7d90bd01b88bfb860dd6d3eed
  while True:
    rgb = file.read(4)
    if len(rgb) != 4 or rgb == '':
      break
<<<<<<< HEAD
    data = rgb[0]<<16 | rgb[1]<<8 | rgb[2]
    by = data >> 12 
    bx = data & 0x00000FFF
    a.append((by, bx))
  return np.array(a)

def getANND(filepath):
  file = read(filepath, 'rb')
  a = []
  while True:
    rgb = file.read(3)
    if rgb == '':
      break
    data = rgb[0]<<16 | rgb[1]<<8 | rgb[2]
    a.append(data)
  return np.array(a)
=======
    else:
      rgb = map(ord, rgb)
    data = rgb[2]<<16 | rgb[1]<<8 | rgb[0]
    annd.append(data)
  file.close()

  return np.array(ann), np.array(annd)
>>>>>>> a0ce5d9b48285ce7d90bd01b88bfb860dd6d3eed
