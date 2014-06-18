import NNF_dll
import numpy as np
import cv2
import matplotlib.pyplot as pl
import scipy.ndimage

a=pl.imread("../image/dog.jpg")
bitmap1=NNF_dll.np2Bitmap(a)
b=cv2.resize(a, (a.shape[0], a.shape[1]*0.9))

=NNF_dll.patchmatch(a,b)

