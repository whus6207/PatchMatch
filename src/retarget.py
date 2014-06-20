import NNF_dll
import numpy as np
import cv2
import matplotlib.pyplot as pl
import scipy.ndimage as sci
import math

def retarget(a1, w_ratio, h_ratio):
    patch_size=7
    #w_rate=0.95
    #h_rate=1
    NNF_dll.setPatchW(patch_size)
    a1=a1[::2,::2,:3][::2, ::2]
    print 'origin image shape', a1.shape
    a=np.zeros((a1.shape[0]+patch_size-1, a1.shape[1]+patch_size-1, 3), dtype=a1.dtype)
    a[patch_size/2 : -patch_size/2+1, patch_size/2 : -patch_size/2+1]=a1
    bitmap1=NNF_dll.np2Bitmap(a)

    targetShape = [a.shape[0]*h_ratio, a.shape[1]*w_ratio]

    #b1=cv2.resize(a1,  (int(a1.shape[1]*w_rate), int(a1.shape[0]*h_rate)))
    b = a1
    
    print "before", a.shape, b.shape
    print "targetShape", targetShape
    while True:
        if w_ratio>1 or h_ratio>1:
            break

        w_rate = max(0.95, w_ratio)
        h_rate = max(0.95, h_ratio)

        b1=cv2.resize(b,  (int(b.shape[1]*w_rate), int(b.shape[0]*h_rate)))
        b =np.zeros((b1.shape[0]+patch_size-1,b1.shape[1]+patch_size-1,3), dtype=b1.dtype)
        b[patch_size/2:-patch_size/2+1, patch_size/2:-patch_size/2+1]=b1
    

        if b.shape[0] < targetShape[0] or b.shape[1] < targetShape[1]:
            if not b.shape[0]<targetShape[0]:
                w_rate=1
            elif not b.shape[1]<targetShape[1]:
                h_rate=1
            else:
                break
        #pl.imshow(b)
        #pl.show()
        #pl.imshow(b1)
        #pl.show()
        #print "b1 shape=", b1.shape


        print "a shape=", a.shape
        print "b shape=", b.shape

        #pl.imshow(b)
        #pl.show()
        bitmap2=NNF_dll.np2Bitmap(b)
        com_ann, com_annd=NNF_dll.patchmatchc(bitmap1,bitmap2)
        coh_ann, coh_annd=NNF_dll.patchmatchc(bitmap2,bitmap1)

        com_map=[[[] for j in range(b.shape[1])] for i in range(b.shape[0])]

        # build mapping for complete match
        for i in range(b.shape[0]):
            for j in range(b.shape[1]):
                com_map[int(com_ann[i][j][0])][int(com_ann[i][j][1])].append(com_ann[i][j].tolist())

        Ns=(a.shape[0]-patch_size)*(a.shape[1]-patch_size)*1.0
        Nt=(b.shape[0]-patch_size)*(b.shape[1]-patch_size)*1.0
        m=(patch_size)**2
        # calculate value of each pixel
        for i in range(patch_size/2, b.shape[0]-(patch_size/2)):
            for j in range(patch_size/2, b.shape[1]-(patch_size/2)):
                p_com = np.zeros(3)
                p_coh = np.zeros(3)
                n=0#len(com_map[i][j])

                #for k in range(n):
                #    p_com+=a[ int(com_map[i][j][k][0]) , int(com_map[i][j][k][1]) ]
                #for x in range (1):
                for x in range (-(patch_size/2), patch_size/2+1):
                    #for y in range (1):
                    for y in range (-(patch_size/2), patch_size/2+1):
                        if coh_ann[i+x][j+y][1]-x>a.shape[1]-patch_size/2 or coh_ann[i+x][j+y][1]-x<patch_size/2:
                            #print (coh_ann[i+x][j+y]), i,j, x, y
                            continue
                        if coh_ann[i+x][j+y][0]-y>a.shape[0]-patch_size/2 or coh_ann[i+x][j+y][1]-y<patch_size/2:
                            #print (coh_ann[i+x][j+y]), i,j, x, y
                            continue
                        p_coh+=a[ int(coh_ann[i+x][j+y][0])-x , int(coh_ann[i+x][j+y][1])-y ]

                b[i][j]=((p_com/Ns+p_coh/Nt)/(n/Ns+m/Nt)).astype("int32")
        b=b[patch_size/2:-patch_size/2, patch_size/2:-patch_size/2]
        print "b shape after crop: ", b.shape


    pl.subplot(2,1,1).imshow(b)
    #print type(b)
    # pl.subplot(2,1,1).imshow(b)
    #b=b[:-patch_size, :-patch_size]
    #pl.subplot(num_it/2+1,2,num_it+2).imshow(a)
    pl.subplot(2,1,2).imshow(a)
    pl.show()
    return b

def main():
    a=pl.imread("../image/seam_carving.jpg")
    retarget(a,0.9,1)

if __name__=="__main__":
    main()
