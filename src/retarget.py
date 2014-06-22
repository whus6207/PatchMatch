import NNF_dll
import numpy as np
import cv2
import matplotlib.pyplot as pl
import scipy.ndimage as sci
import math
from inpaint import *

def retarget(a1, w_ratio, h_ratio):
    patch_size=7
    slow=False

    #PlayerQueue = Queue.Queue()
    #running = [True]
    #Player = App(PlayerQueue, running)
    #Player.start()

    #w_rate=0.95
    #h_rate=1
    NNF_dll.setPatchW(patch_size)
    a1=a1[::2,::2,:3]
    a=np.zeros((a1.shape[0]+patch_size-1, a1.shape[1]+patch_size-1, 3), dtype=a1.dtype)
    a[patch_size/2 : -patch_size/2+1, patch_size/2 : -patch_size/2+1]=a1
    bitmap1=NNF_dll.np2Bitmap(a)

    targetShape = [a.shape[0]*h_ratio, a.shape[1]*w_ratio]

    #b1=cv2.resize(a1,  (int(a1.shape[1]*w_rate), int(a1.shape[0]*h_rate)))
    b = a1
    start=time.time() 
    while True:
        print "a shape", a.shape
        print "b shape", b.shape
        if w_ratio>1 or h_ratio>1:
            break

        w_rate = max(0.95, w_ratio)
        h_rate = max(0.95, h_ratio)

        
        if b.shape[0] < targetShape[0] or b.shape[1] < targetShape[1]:
            if not b.shape[0]<targetShape[0]:
                w_rate=1
            elif not b.shape[1]<targetShape[1]:
                h_rate=1
            else:
                break
        b1=cv2.resize(b,  (int(b.shape[1]*w_rate), int(b.shape[0]*h_rate)))
        b =np.zeros((b1.shape[0]+patch_size-1,b1.shape[1]+patch_size-1,3), dtype=b1.dtype)
        b[patch_size/2:-patch_size/2+1, patch_size/2:-patch_size/2+1]=b1

        #pl.imshow(b)
        #pl.show()
        #pl.imshow(b1)
        #pl.show()
        #print "b1 shape=", b1.shape



        #pl.imshow(b)
        #pl.show()
        bitmap2=NNF_dll.np2Bitmap(b)
        com_ann, com_annd=NNF_dll.patchmatchc(bitmap1,bitmap2)
        coh_ann, coh_annd=NNF_dll.patchmatchc(bitmap2,bitmap1)

        if slow:
            com_map=[[[] for j in range(b.shape[1])] for i in range(b.shape[0])]

            # build mapping for complete match
            for i in range(patch_size/2, a.shape[0]-(patch_size/2)):
                for j in range(patch_size/2, a.shape[1]-(patch_size/2)):
                    com_map[int(com_ann[i][j][0])][int(com_ann[i][j][1])].append(np.array([i,j]).tolist())
        
        Ns=(a.shape[0]-patch_size)*(a.shape[1]-patch_size)*1.0
        Nt=(b.shape[0]-patch_size)*(b.shape[1]-patch_size)*1.0
        # calculate value of each pixel
        s = time.time()
        
        if not slow:
            com_value=np.zeros((b.shape[0], b.shape[1], 3), dtype=np.int32)
            coh_value=np.zeros((b.shape[0], b.shape[1], 3), dtype=np.int32)
            m_value=np.zeros((b.shape[0], b.shape[1],3), dtype=np.int32)
            n_value=np.zeros((b.shape[0], b.shape[1],3), dtype=np.int32)
            b_temp=np.zeros((b.shape[0], b.shape[1], 3), dtype=b.dtype)

            #n_value+=patch_size**2
            
            for i in range (patch_size/2, com_ann.shape[0]-(patch_size/2)):
                for j in range (patch_size/2, com_ann.shape[1]-(patch_size/2)):
                    if com_ann[i,j][0]>b.shape[0]-(patch_size/2) or com_ann[i,j][1]>b.shape[1]-(patch_size/2):
                        continue
                    com_value[int(com_ann[i][j][0])-(patch_size/2):int(com_ann[i][j][0])+patch_size/2
                            , int(com_ann[i][j][1])-(patch_size/2):int(com_ann[i][j][1])+patch_size/2]+=a[i-(patch_size/2):i+patch_size/2, j-(patch_size/2):j+patch_size/2]
                    m_value[int(com_ann[i][j][0])-(patch_size/2):int(com_ann[i][j][0])+patch_size/2
                            , int(com_ann[i][j][1])-(patch_size/2):int(com_ann[i][j][1])+patch_size/2]+=1
            
            for i in range (patch_size/2, coh_ann.shape[0]-(patch_size/2)):
                for j in range (patch_size/2, coh_ann.shape[1]-(patch_size/2)):
                    if coh_ann[i,j][0]>a.shape[0]-(patch_size/2) or coh_ann[i,j][1]>a.shape[1]-(patch_size/2):
                        continue
                    coh_value[i-(patch_size/2):i+patch_size/2, j-(patch_size/2):j+patch_size/2]+=a[int(coh_ann[i][j][0])-(patch_size/2):int(coh_ann[i][j][0])+patch_size/2
                            , int(coh_ann[i][j][1])-(patch_size/2):int(coh_ann[i][j][1])+patch_size/2]
                    n_value[i-(patch_size/2):i+patch_size/2, j-(patch_size/2):j+patch_size/2]+=1
            
            b_temp=(com_value/Ns+coh_value/Nt)/(m_value/Ns+n_value/Nt)
            #b_temp=((coh_value/Nt)/(n_value/Nt))
            b=b_temp.astype("uint8")
            b=b[patch_size/2:-patch_size/2, patch_size/2:-patch_size/2]
        
        if slow:
            for i in range(patch_size/2, b.shape[0]-(patch_size/2)):
                for j in range(patch_size/2, b.shape[1]-(patch_size/2)):
                    p_com = np.zeros(3)
                    p_coh = np.zeros(3)
                    n=len(com_map[i][j])
                    m=(patch_size)**2
                    num_com=0
                    if n>0:
                        #for x in range (1):
                        for x in range (-(patch_size/2), patch_size/2+1):
                            #for y in range (1):
                            for y in range (-(patch_size/2), patch_size/2+1):
                                #print i,j, k, x, y,n
                                #print com_map[i+x][j+y]
                                for z in range(len(com_map[i+x][j+y])):
                                    if len(com_map[i+x][j+y])==0:
                                        continue
                                    if com_map[i+x][j+y][z][0]-x>a.shape[0]-patch_size/2 or com_map[i+x][j+y][z][0]-x<patch_size/2:
                                        continue
                                    if com_map[i+x][j+y][z][1]-y>a.shape[1]-patch_size/2 or com_map[i+x][j+y][z][1]-y<patch_size/2:
                                        continue
                                    num_com+=1
                                    p_com+=a[ int(com_map[i+x][j+y][z][0]-x) , int(com_map[i+x][j+y][z][1]-y) ]
                    
                    #for x in range (1):
                    for x in range (-(patch_size/2), patch_size/2+1):
                        #for y in range (1):
                        for y in range (-(patch_size/2), patch_size/2+1):
                            if coh_ann[i+x][j+y][0]-x>a.shape[0]-patch_size/2 or coh_ann[i+x][j+y][0]-x<patch_size/2:
                                #print (coh_ann[i+x][j+y]), i,j, x, y
                                m-=1
                                continue
                            if coh_ann[i+x][j+y][1]-y>a.shape[1]-patch_size/2 or coh_ann[i+x][j+y][1]-y<patch_size/2:
                                #print (coh_ann[i+x][j+y]), i,j, x, y
                                m-=1
                                continue
                            p_coh+=a[ int(coh_ann[i+x][j+y][0])-x , int(coh_ann[i+x][j+y][1])-y ]

                    b[i][j]=((p_com/Ns+p_coh/Nt)/(num_com/Ns+m/Nt)).astype("int32")
            #    PlayerQueue.put(cv2.resize(b.copy(), (b.shape[1]*4, b.shape[0]*4)))
            b=b[patch_size/2:-patch_size/2, patch_size/2:-patch_size/2]

        print "time for this iteration: ", time.time()-s
        #pl.imshow(b)
        #pl.show()
    
    #if slow:
    #    while PlayerQueue.qsize() != 0 and running:
    #        time.sleep(0)
    #    running.pop()
        
    pl.subplot(2,1,1).imshow(b)
    #print type(b)
    # pl.subplot(2,1,1).imshow(b)
    #b=b[:-patch_size, :-patch_size]
    #pl.subplot(num_it/2+1,2,num_it+2).imshow(a)
    print "total time: ", time.time()-start
    pl.subplot(2,1,2).imshow(a1)
    pl.show()
    return b

def main():
    a=pl.imread("../image/seam_carving.jpg")
    retarget(a,0.6,1)

if __name__=="__main__":
    main()
