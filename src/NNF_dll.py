from ctypes import *
import numpy as np
import time
import os

def getGlobalInt(dll, name):
    return c_int.in_dll(dll, name)

def np2Pointer(arr, type):
    return arr.ctypes.data_as(POINTER(type))

#define struct
class BITMAP(Structure):
    _fields_ = [
        ('w', c_int),
        ('h', c_int),
        ('data', POINTER(c_int))
               ]

    def area(self):
        return self.w * self.h

    def __str__(self):
        return "BITMAP CLASS, w: %d, h: %d"%(self.w, self.h)


dll = None
dllc = None

def loadDll():
    global dll
    global dllc
    #load dll and get the function object
    dll = CDLL(os.getcwd() + "/NNF.dll")
    # np.ctypeslib.load_library(NNFDllPath, ".")
    dll.GetBitMap.restype = POINTER(BITMAP)
    dll.GetBitMap.argtypes = [c_int, c_int, POINTER(c_int)];

    dll.dist.restype = c_int
    dll.dist.argtypes = [POINTER(BITMAP), POINTER(BITMAP), c_int, c_int, c_int, c_int]

    dll.patchmatch.restype = None
    dll.patchmatch.argtype = [POINTER(BITMAP), POINTER(BITMAP), POINTER(POINTER(BITMAP)), POINTER(POINTER(BITMAP)), c_int]

    dll.maskPatchMatch.restype = None
    dll.maskPatchMatch.argtype = [POINTER(BITMAP), POINTER(BITMAP), POINTER(POINTER(BITMAP)), POINTER(POINTER(BITMAP)), c_int, POINTER(BITMAP)]

    dll.test.restype = c_int
    dll.test.argtype = [POINTER(c_int)]

    dll.setPatchW.restype = c_int
    dll.setPatchW.argtype = [c_int]

    dllc = CDLL(os.getcwd() + "/NNF_center.dll")
    # np.ctypeslib.load_library(NNFDllPath, ".")
    dllc.GetBitMap.restype = POINTER(BITMAP)
    dllc.GetBitMap.argtypes = [c_int, c_int, POINTER(c_int)];

    dllc.dist.restype = c_int
    dllc.dist.argtypes = [POINTER(BITMAP), POINTER(BITMAP), c_int, c_int, c_int, c_int]

    dllc.patchmatch.restype = None
    dllc.patchmatch.argtype = [POINTER(BITMAP), POINTER(BITMAP), POINTER(POINTER(BITMAP)), POINTER(POINTER(BITMAP))]

    dllc.test.restype = c_int
    dllc.test.argtype = [POINTER(c_int)]

    dllc.setPatchW.restype = c_int
    dllc.setPatchW.argtype = [c_int]

loadDll()

def setPatchW(i):
    return dll.setPatchW(i)

def np2Bitmap(arr):
    arr = arr.astype('int32')
    data = (arr[:, :, 0] | arr[:, :, 1]<<8 | arr[:, :, 2]<<16 ).flatten() | 255 << 24
    data = (c_int * len(data))(*data)
    return dll.GetBitMap(arr.shape[1], arr.shape[0], data)

def patchmatch(bitmap1, bitmap2, rotation=0, benchmark=True, mask=None):
    global times
    ann = POINTER(BITMAP)()
    annd = POINTER(BITMAP)()
    if benchmark:
        start = time.time()
    if mask:
        dll.maskPatchMatch(bitmap1, bitmap2, byref(ann), byref(annd), rotation*90, mask)
    else:
        dll.patchmatch(bitmap1, bitmap2, byref(ann), byref(annd), rotation*90)
    if benchmark:
        print 'cost', time.time() - start, 'seconds'

    # convert ann to numpy array
    temp = np.zeros((bitmap1.contents.area(), 2))
    for i in range(bitmap1.contents.w*bitmap1.contents.h):
        temp[i] = [ann.contents.data[i]>>12, ann.contents.data[i]&0xfff]
    ann = temp.reshape((bitmap1.contents.h, bitmap1.contents.w, 2))

    # convert annd to numpy array
    temp = np.zeros(bitmap1.contents.area())
    for i in range(bitmap1.contents.w*bitmap1.contents.h):
        temp[i] = annd.contents.data[i]
    annd = temp.reshape((bitmap1.contents.h, bitmap1.contents.w))
    return ann, annd

def patchmatchc(bitmap1, bitmap2, benchmark=True):
    global times
    ann = POINTER(BITMAP)()
    annd = POINTER(BITMAP)()
    if benchmark:
        start = time.time()
    dllc.patchmatch(bitmap1, bitmap2, byref(ann), byref(annd), 0)
    if benchmark:
        print 'cost', time.time() - start, 'seconds'

    # convert ann to numpy array
    temp = np.zeros((bitmap1.contents.area(), 2))
    for i in range(bitmap1.contents.w*bitmap1.contents.h):
        temp[i] = [ann.contents.data[i]>>12, ann.contents.data[i]&0xfff]
    ann = temp.reshape((bitmap1.contents.h, bitmap1.contents.w, 2))

    # convert annd to numpy array
    temp = np.zeros(bitmap1.contents.area())
    for i in range(bitmap1.contents.w*bitmap1.contents.h):
        temp[i] = annd.contents.data[i]
    annd = temp.reshape((bitmap1.contents.h, bitmap1.contents.w))
    return ann, annd    


def main(tt='block.jpg', tt2='../image/example.jpg'):
    # test utility
    w = POINTER(c_int)()
    dll.test(byref(w))
    for i in range(10):
        if w[i] != 100-i:
            print 'test error!!, w[%d]=%d'%(i, w[i])
            exit(1)
    print 'test finish, all correct'.center(100, '-')


    # load image data
    import matplotlib.pyplot as npl
    data1 = npl.imread(tt)
    data2 = npl.imread(tt2)

    # convert to Bitmap data
    bitmap1 = np2Bitmap(data1)
    bitmap2 = np2Bitmap(data2)

    # check data
    print 'data1: ', bitmap1.contents
    print 'data2: ', bitmap2.contents
    print 'check distance function'.center(100, '-')
    print 'dist (10,18) -> (10, 18): ', dll.dist(bitmap1, bitmap2, 10, 18, 10, 18)
    print ('all checked, NNF for file %s, %s'%(tt, tt2)).center(100, '-')

    for rot in range(4):
        print rot
        ann, annd = patchmatch(bitmap1, bitmap2, rot)
        rebuild = np.zeros_like(data1)
        for i in range(rebuild.shape[0]):
            for j in range(rebuild.shape[1]):
                rebuild[i, j] = data2[ann[i,j,0], ann[i,j,1]]
        
        npl.subplot(5,3, rot*3 + 1).imshow(data1)
        npl.subplot(5,3, rot*3 + 2).imshow(data2)
        npl.subplot(5,3, rot*3 + 3).imshow(rebuild.copy())

    ann, annd = patchmatchc(bitmap1, bitmap2)
    rebuild = np.zeros_like(data1)
    for i in range(rebuild.shape[0]):
        for j in range(rebuild.shape[1]):
            rebuild[i, j] = data2[ann[i,j,0], ann[i,j,1]]
    npl.subplot(5,3,13).imshow(rebuild)
    npl.show()

if __name__ == "__main__":
    main()
