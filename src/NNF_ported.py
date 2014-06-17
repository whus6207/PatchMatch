import numpy as np
import random
import time
import numexpr as ne

INT_MAX = 0xfffff
patch_w  = 5
pm_iters = 5
rs_max   = INT_MAX

def dist(a, b, ax, ay, bx, by, cutoff=INT_MAX):
  ans = 0
  ac = a[ay:ay+patch_w, ax:ax+patch_w]
  bc = b[by:by+patch_w, bx:bx+patch_w]
 
  ans = ((1.0*ac - bc)**2).sum()
  if ans >= cutoff:
    return cutoff
  return ans

def improve_guess(a, b, ax, ay, xbest, ybest, dbest, bx, by):
  d = dist(a, b, ax, ay, bx, by, dbest)
  if d < dbest:
    # print 'improved_guess', dbest, '->', d
    dbest = d
    xbest = bx
    ybest = by
  return xbest, ybest, dbest

def patchmatch_core(a, b, ann, annd, ay, ax, xchange, ychange, aew, bew, aeh, beh):
  # Current (best) guess.
  ybest, xbest = ann[ay, ax]
  dbest = annd[ay, ax]
  oriPos = ybest, xbest

  # Propagation: Improve current guess by trying instead correspondences from left and above (below and right on odd iterations).
  if (ax - xchange) < aew:
    yp, xp = ann[ay, ax-xchange]
    if xp < bew:
      xbest, ybest, dbest = improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp)

  if (ay - ychange) < aeh:
    yp, xp = ann[ay-ychange, ax]
    if yp < beh:
      xbest, ybest, dbest = improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp)

  #  search: Improve current guess by searching in boxes of exponentially decreasing size around the current best guess.
  mag = min(rs_max, max(b.shape[1], b.shape[0]))
  while mag >= 1:
    # Sampling window
    xmin = max(xbest-mag, 0)
    xmax = min(xbest+mag+1, bew)
    ymin = max(ybest-mag, 0)
    ymax = min(ybest+mag+1, beh)
    xp = xmin + random.randint(0, xmax-xmin-1)
    yp = ymin + random.randint(0, ymax-ymin-1)
    xbest, ybest, dbest = improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp)          
    mag >>= 2

  
  ann[ay, ax] = [ybest, xbest]
  annd[ay, ax] = dbest
  if oriPos != (ybest, xbest):
    return 1
  else:
    return 0

# Match image a to image b, returning the nearest neighbor field mapping a => b coords, stored in an RGB 24-bit image as (by<<12)|bx.
def patchmatch(a, b):
  # Effective width and height (possible upper left corners of patches).
  aew = a.shape[1] - patch_w + 1
  aeh = a.shape[0] - patch_w + 1
  bew = b.shape[1] - patch_w + 1
  beh = b.shape[0] - patch_w + 1

  # Initialize with random nearest neighbor field (NNF).
  ann = np.random.rand(a.shape[0], a.shape[1], 2)
  ann[:, :, 0] *= beh
  ann[:, :, 1] *= bew
  ann = ann.astype('int32')
  annd = np.zeros((a.shape[0], a.shape[1]))*1.0
  print 'random init'
  for ay in range(aeh):
    for ax in range(aew):
      by, bx = ann[ay, ax]
      annd[ay, ax] = dist(a, b, ax, ay, bx, by)

  for iter in range(pm_iters):
    print 'running iteration: %d/%d'%(iter, pm_iters)
    # In each iteration, improve the NNF, by looping in scanline or reverse-scanline order.
    ystart = xstart = 0
    ychange = xchange = 1
    yend = aeh 
    xend = aew

    # In odd turn, travese with inverse order
    if iter % 2 == 1:
      xstart = xend - 1
      ystart = yend - 1
      xend = yend = -1
      xchange = ychange = -1

    update = 0
    start_time = time.time()

    for ay in range(ystart, yend, ychange):
      for ax in range(xstart, xend, xchange):
        patchmatch_core(a, b, ann, annd, ay, ax, xchange, ychange, aew, bew, aeh, beh)

    print '%d pixels updated, '%update, 'annd.mean():', annd.mean()
    print 'iteration:', time.time() - start_time, 'seconds'
  return ann, annd


def main():
  import matplotlib.pyplot as npl
  tt = 'block.jpg'
  tt2 = '../image/example.jpg'
  # tt2 = tt

  img1 = npl.imread(tt)
  img2 = npl.imread(tt2)
  start_time = time.time()
  ann, annd = patchmatch(img1, img2)
  print ann
  print 'total', time.time() - start_time, 'seconds'
  t = np.zeros_like(img1, dtype=img1.dtype)
  for i in range(ann.shape[0]):
    for j in range(ann.shape[1]):
      t[i, j] = img2[ann[i, j][0], ann[i][j][1]]

  npl.subplot(3,1,1).imshow(t)
  npl.subplot(3,1,2).imshow(img1)
  npl.subplot(3,1,3).imshow(img2)
  npl.show()


if __name__ == "__main__":
  main()
