#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef MAX
#define MAX(a, b) ((a)>(b)?(a):(b))
#define MIN(a, b) ((a)<(b)?(a):(b))
#endif

#define INT_MAX 0xffffff
#define XY_TO_INT(x, y) (((y)<<12)|(x))
#define INT_TO_X(v) ((v)&((1<<12)-1))
#define INT_TO_Y(v) ((v)>>12)


int patch_w  = 7;
int pm_iters = 10;
int rs_max   = INT_MAX;

class BITMAP { public:
  int w, h;
  int *data;
  BITMAP(int w_, int h_) :w(w_), h(h_) { data = new int[w*h]; }
  ~BITMAP() { delete[] data; }
  int *operator[](int y) { return &data[y*w]; }
};


BITMAP *maskedMap = NULL;
extern "C" {
  BITMAP *GetBitMap(int w, int h, int *data){
    BITMAP *bitmap = new BITMAP(w, h);
    
    int *p = bitmap->data;
    for(int i=0; i<w*h; i++)
      *p++ = data[i];

    return bitmap;
  }

  int test(int *&data){
    data = new int[maskedMap->w*maskedMap->h];
    for (int dy = 0; dy < maskedMap->h; dy++)
      for (int dx = 0; dx < maskedMap->w; dx++) {
        data[dy*maskedMap->w + dx] = maskedMap->data[dy*maskedMap->w + dx];
      }
    return 0;
  }

  int setPatchW(int i){
    patch_w = i;
    return patch_w;
  }

  int setMaskedArea(int w, int h, int *data){
    BITMAP *bitmap = new BITMAP(w, h);
    int *p = bitmap->data;
    for(int i=0; i<w*h; i++)
      *p++ = data[i];

    if (maskedMap)
      delete maskedMap;
    maskedMap = bitmap;
    return 0;
  }

  int dist(BITMAP *a, BITMAP *b, int ax, int ay, int bx, int by, int cutoff);

  void patchmatch(BITMAP *a, BITMAP *b, BITMAP *&ann, BITMAP *&annd);
}

int dist(BITMAP *a, BITMAP *b, int ax, int ay, int bx, int by, int cutoff=INT_MAX) {
  int start = -(patch_w/2), end = patch_w/2 + 1;
  // Calculate usable pixels
  double ans = 0;
  double Nbr = 0;

  if (maskedMap->data[(by)*maskedMap->w + bx] > 10)
    return cutoff;

  for (int dy = start; dy < end; dy++) {
    int *arow = &(*a)[ay+dy][ax];
    int *brow = &(*b)[by+dy][bx];
    for (int dx = start; dx < end; dx++) {
      int ac = arow[dx];
      int bc = brow[dx];
      int dr = (ac&255)-(bc&255);
      int dg = ((ac>>8)&255)-((bc>>8)&255);
      int db = (ac>>16)-(bc>>16);

      if (maskedMap->data[(by+dy)*maskedMap->w + bx + dx] < 10 && maskedMap->data[(ay+dy)*maskedMap->w + ax + dx] < 10){
        Nbr += 1;
        ans += dr*dr + dg*dg + db*db;
      }
    }
  }
  if (Nbr < patch_w*patch_w/3.)
    return cutoff;
  ans = ans/Nbr;
  return (int)ans;
}

void improve_guess(BITMAP *a, BITMAP *b, int ax, int ay, int &xbest, int &ybest, int &dbest, int bx, int by) {
  int d = dist(a, b, ax, ay, bx, by, dbest);
  if (d < dbest) {
    dbest = d;
    xbest = bx;
    ybest = by;
  }
}

/* Match image a to image b, returning the nearest neighbor field mapping a => b coords, stored in an RGB 24-bit image as (by<<12)|bx. */
void patchmatch(BITMAP *a, BITMAP *b, BITMAP *&ann, BITMAP *&annd) {
  /* Initialize with random nearest neighbor field (NNF). */
  ann = new BITMAP(a->w, a->h);
  annd = new BITMAP(a->w, a->h);


  int aew = a->w - patch_w/2, aeh = a->h - patch_w/2;       /* Effective width and height (possible upper left corners of patches). */
  int bew = b->w - patch_w/2, beh = b->h - patch_w/2;
  memset(ann->data, 0, sizeof(int)*a->w*a->h);
  memset(annd->data, 0, sizeof(int)*a->w*a->h);
  for (int ay = patch_w/2; ay < aeh; ay++) {
    for (int ax = patch_w/2; ax < aew; ax++) {
      int bx = patch_w/2 +  rand()%bew;
      int by = patch_w/2 +  rand()%beh;
      (*ann)[ay][ax] = XY_TO_INT(bx, by);
      (*annd)[ay][ax] = dist(a, b, ax, ay, bx, by);
    }
  }
  // return;

  for (int iter = 0; iter < pm_iters; iter++) {
    /* In each iteration, improve the NNF, by looping in scanline or reverse-scanline order. */
    // fprintf(f, "iter: %d/%d\n", iter, pm_iters);
    int ystart = patch_w/2, yend = aeh, ychange = 1;
    int xstart = patch_w/2, xend = aew, xchange = 1;
    if (iter % 2 == 1) {
      xstart = xend-1; xend = patch_w/2-1; xchange = -1;
      ystart = yend-1; yend = patch_w/2-1; ychange = -1;
    }
    
    for (int ay = ystart; ay != yend; ay = ay + ychange) {
      for (int ax = xstart; ax != xend; ax += xchange) { 
        /* Current (best) guess. */
        int v = (*ann)[ay][ax];
        int xbest = INT_TO_X(v), ybest = INT_TO_Y(v);
        int dbest = (*annd)[ay][ax];

        /* Propagation: Improve current guess by trying instead correspondences from left and above (below and right on odd iterations). */
        if ((unsigned) (ax - xchange) < (unsigned) aew) {
          int vp = (*ann)[ay][ax-xchange];
          int xp = INT_TO_X(vp) + xchange, yp = INT_TO_Y(vp);
          if ((unsigned) xp < (unsigned) bew && (unsigned) xp >= patch_w/2) {
            improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp);
          }
        }

        if ((unsigned) (ay - ychange) < (unsigned) aeh) {
          int vp = (*ann)[ay-ychange][ax];
          int xp = INT_TO_X(vp), yp = INT_TO_Y(vp) + ychange;
          if ((unsigned) yp < (unsigned) beh && (unsigned) yp >= patch_w/2) {
            improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp);
          }
        }



        /* Random search: Improve current guess by searching in boxes of exponentially decreasing size around the current best guess. */
        int rs_start = rs_max;
        if (rs_start > MAX(b->w, b->h)) { rs_start = MAX(b->w, b->h); }
        for (int mag = rs_start; mag >= 1; mag /= 2) {
          /* Sampling window */
          int xmin = MAX(xbest-mag, patch_w/2), xmax = MIN(xbest+mag+1,bew);
          int ymin = MAX(ybest-mag, patch_w/2), ymax = MIN(ybest+mag+1,beh);
          if (xmax <= xmin)
            continue;
          if (ymax <= ymin)
            continue;

          int xp = xmin+rand()%(xmax-xmin);
          int yp = ymin+rand()%(ymax-ymin);
          improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp);
        }

        (*ann)[ay][ax] = XY_TO_INT(xbest, ybest);
        (*annd)[ay][ax] = dbest;
      }
    }
    return;
  }
}
