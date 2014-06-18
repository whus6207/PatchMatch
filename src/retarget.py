import NNF_dll
import numpy as np
import cv2
import matplotlib.pyplot as pl
import scipy.ndimage
import math

num_it=15
patch_size=7
w_rate=0.95
h_rate=0.95
NNF_dll.setPatchW(7)
a=pl.imread("../image/seam_carving.jpg")[::2, ::2][::2, ::2][::2, ::2]
bitmap1=NNF_dll.np2Bitmap(a)
b=cv2.resize(a,  (int(a.shape[1]*h_rate), int(a.shape[0]*w_rate) ))

print "a shape=", a.shape
print "b shape=", b.shape

for it in range(num_it):
    bitmap2=NNF_dll.np2Bitmap(b)
    com_ann, com_annd=NNF_dll.patchmatch(bitmap1,bitmap2)
    coh_ann, coh_annd=NNF_dll.patchmatch(bitmap2,bitmap1)

    com_map=[[[] for j in range(b.shape[1])] for i in range(b.shape[0])]

    # build mapping for complete match
    for i in range(b.shape[0]):
        for j in range(b.shape[1]):
            com_map[int(com_ann[i][j][0])][int(com_ann[i][j][1])].append(com_ann[i][j].tolist())

    Ns=(a.shape[0]-patch_size)*(a.shape[1]-patch_size)*1.0
    Nt=(b.shape[0]-patch_size)*(b.shape[1]-patch_size)*1.0
    m=patch_size**2
    # calculate value of each pixel
    for i in range(b.shape[0]-patch_size):
        for j in range(b.shape[1]-patch_size):
            p_com = np.zeros(3)
            p_coh = np.zeros(3)
            n=len(com_map[i][j])

            for k in range(n):
                p_com+=a[ int(com_map[i][j][k][0]) ][ int(com_map[i][j][k][1]) ]
            for x in range(i, i+patch_size):
                for y in range(j, j+patch_size):
                    p_coh+=a[ int(coh_ann[x][y][0]) ][ int(coh_ann[x][y][1]) ]

            b[i][j]=((p_com/Ns+p_coh/Nt)/(n/Ns+m/Nt)).astype("int32")

print b.shape
b=b[:-patch_size, :-patch_size]
pl.subplot(3,1,1).imshow(a)
pl.subplot(3,1,2).imshow(b)
pl.subplot(3,1,3).imshow(cv2.resize(a,(int(a.shape[1]*h_rate), int(a.shape[0]*w_rate))))
pl.show()
exit(1)
