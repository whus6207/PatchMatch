
/* -------------------------------------------------------------------------
  Minimal (unoptimized) example of PatchMatch. Requires that ImageMagick be installed.

  To improve generality you can:
   - Use whichever distance function you want in dist(), e.g. compare SIFT descriptors computed densely.
   - Search over a larger search space, such as rotating+scaling patches (see MATLAB mex for examples of both)
  
  To improve speed you can:
   - Turn on optimizations (/Ox /Oi /Oy /fp:fast or -O6 -s -ffast-math -fomit-frame-pointer -fstrength-reduce -msse2 -funroll-loops)
   - Use the MATLAB mex which is already tuned for speed
   - Use multiple cores, tiling the input. See our publication "The Generalized PatchMatch Correspondence Algorithm"
   - Tune the distance computation: manually unroll loops for each patch size, use SSE instructions (see readme)
   - Precompute random search samples (to avoid using rand, and mod)
   - Move to the GPU
  -------------------------------------------------------------------------- */

#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef MAX
#define MAX(a, b) ((a)>(b)?(a):(b))
#define MIN(a, b) ((a)<(b)?(a):(b))
#endif

#define INT_MAX 99999999
#define XY_TO_INT(x, y) (((y)<<12)|(x))
#define INT_TO_X(v) ((v)&((1<<12)-1))
#define INT_TO_Y(v) ((v)>>12)


int patch_w  = 7;
int pm_iters = 10;
int rs_max   = INT_MAX;
int rotation = 0;


/* -------------------------------------------------------------------------
   BITMAP: Minimal image class
   ------------------------------------------------------------------------- */

class BITMAP { public:
  int w, h;
  int *data;
  BITMAP(int w_, int h_) :w(w_), h(h_) { data = new int[w*h]; }
  ~BITMAP() { delete[] data; }
  int *operator[](int y) { return &data[y*w]; }
};


// #ifdef EXPORT_DLL
// #define DLLAPI __declspec(dllexport)
  extern "C" {
    BITMAP *GetBitMap(int w, int h, int *data){
      BITMAP *bitmap = new BITMAP(w, h);
      
      int *p = bitmap->data;
      for(int i=0; i<w*h; i++)
        *p++ = data[i];

      return bitmap;
    }

    int test(int *&data){
      data = new int[10];
      for (int i=0; i<10; i++)
        data[i] = 100-i;
      return data[0];
    }

    int setPatchW(int i){
      patch_w = i;
      return patch_w;
    }

    int dist(BITMAP *a, BITMAP *b, int ax, int ay, int bx, int by, int cutoff);

    void patchmatch(BITMAP *a, BITMAP *b, BITMAP *&ann, BITMAP *&annd, int rotation);
  }
// #endif

BITMAP *load_bitmap(const char *filename) {
  char rawname[256], txtname[256];
  strcpy(rawname, filename);
  strcpy(txtname, filename);
  if (!strstr(rawname, ".")) { fprintf(stderr, "Error reading image '%s': no extension found\n", filename); exit(1); }
  sprintf(strstr(rawname, "."), ".raw");
  sprintf(strstr(txtname, "."), ".txt");
  char buf[256];
  sprintf(buf, "convert %s rgba:%s", filename, rawname);
  // if (system(buf) != 0) { fprintf(stderr, "Error reading image '%s': ImageMagick convert gave an error\n", filename); exit(1); }
  system(buf);
  sprintf(buf, "identify -format \"%%w %%h\" %s > %s", filename, txtname);
  // if (system(buf) != 0) { fprintf(stderr, "Error reading image '%s': ImageMagick identify gave an error\n", filename); exit(1); }
  system(buf);
  FILE *f = fopen(txtname, "rt");
  if (!f) { fprintf(stderr, "Error reading image '%s': could not read output of ImageMagick identify\n", filename); exit(1); }
  int w = 0, h = 0;
  if (fscanf(f, "%d %d", &w, &h) != 2) { fprintf(stderr, "Error reading image '%s': could not get size from ImageMagick identify\n", filename); exit(1); }
  fclose(f);
  f = fopen(rawname, "rb");
  BITMAP *ans = new BITMAP(w, h);
  unsigned char *p = (unsigned char *) ans->data;

  for (int i = 0; i < w*h*4; i++) {
    int ch = fgetc(f);
    if (ch == EOF) { fprintf(stderr, "Error reading image '%s': raw file is smaller than expected size %dx%dx4\n", filename, w, h, 4); exit(1); }
    *p++ = ch;
  }
  fclose(f);
  return ans;
}

void save_bitmap(BITMAP *bmp, const char *filename) {
  char rawname[256];
  strcpy(rawname, filename);
  if (!strstr(rawname, ".")) { fprintf(stderr, "Error writing image '%s': no extension found\n", filename); exit(1); }
  sprintf(strstr(rawname, "."), ".raw");
  char buf[256];
  FILE *f = fopen(rawname, "wb");
  if (!f) { fprintf(stderr, "Error writing image '%s': could not open raw temporary file\n", filename); exit(1); }
  // unsigned char *p = (unsigned char *) bmp->data;
  // for (int i = 0; i < bmp->w*bmp->h*4; i++) {
  //   if (INT_TO_X(*p) > 4000 || INT_TO_Y(*p) > 4000)
  //     printf("too big at %d: %d,%d", *p, INT_TO_X(*p), INT_TO_Y(*p));
  //   fputc(*p++, f);
  // }
  fwrite(bmp->data, sizeof(int), bmp->w*bmp->h, f);
  fclose(f);
  // sprintf(buf, "convert -size %dx%d -depth 8 rgba:%s %s", bmp->w, bmp->h, rawname, filename);
  // system(buf);
  // if (system(buf) != 0) { fprintf(stderr, "Error writing image '%s': ImageMagick convert gave an error\n", filename); exit(1); }
}

/* -------------------------------------------------------------------------
   PatchMatch, using L2 distance between upright patches that translate only
   ------------------------------------------------------------------------- */


/* Measure distance between 2 patches with upper left corners (ax, ay) and (bx, by), terminating early if we exceed a cutoff distance.
   You could implement your own descriptor here. */
int dist(BITMAP *a, BITMAP *b, int ax, int ay, int bx, int by, int cutoff=INT_MAX) {
  int ans = 0;

  int dxstart, dxend;
  int dystart, dyend;
  if (rotation == 0){
    dxstart = dystart = 0;
    dxend = dyend = patch_w;
  }
  else if(rotation == 90){
    dxstart = -patch_w;
    dystart = 0;
    dxend = 0;
    dyend = patch_w;
  }
  else if(rotation == 180){
    dxstart = -patch_w;
    dystart = -patch_w;
    dxend = 0;
    dyend = 0;
  }
  else if(rotation == 270){
    dxstart = 0;
    dystart = -patch_w;
    dxend = patch_w;
    dyend = 0;
  }
  
  for (int dy = dystart; dy < dyend; dy++) {
    int *arow = &(*a)[ay+dy][ax];
    int *brow = &(*b)[by+dy][bx];
    int *maskedRow = &(maskedArea)[by+dy][bx];
    for (int dx = dxstart; dx < dxend; dx++) {
      int ac = arow[dx];
      int bc = brow[dx];
      int masked = maskedRow[dx];
      if (masked != 0)
        return INT_MAX;
      int dr = (ac&255)-(bc&255);
      int dg = ((ac>>8)&255)-((bc>>8)&255);
      int db = (ac>>16)-(bc>>16);
      ans += dr*dr + dg*dg + db*db;
    }
    if (ans >= cutoff) { return cutoff; }
  }
  return ans;
}

void improve_guess(BITMAP *a, BITMAP *b, int ax, int ay, int &xbest, int &ybest, int &dbest, int bx, int by) {
  int d = dist(a, b, ax, ay, bx, by, dbest);
  if (d < dbest) {
    dbest = d;
    xbest = bx;
    ybest = by;
  }
}
BITMAP maskedArea;
/* Match image a to image b, returning the nearest neighbor field mapping a => b coords, stored in an RGB 24-bit image as (by<<12)|bx. */
void patchmatch(BITMAP *a, BITMAP *b, BITMAP *&ann, BITMAP *&annd, int rot = 0, BITMAP &mArea=NULL) {
  if (mArea != NULL) 
    maskedArea = mArea;
  else {
    maskedArea = BITMAP(a->w, a->h)
    memset(maskedArea.data, 0, sizeof(int)*maskedArea.w*maskedArea.h);
  }

  rotation = rot;
  /* Initialize with random nearest neighbor field (NNF). */
  ann = new BITMAP(a->w, a->h);
  annd = new BITMAP(a->w, a->h);

  int aews, aehs, aewe, aehe;
  int bews, behs, bewe, behe;

  /* Effective width and height (possible upper left corners of patches). */
  aews = aehs = bews = behs = 0;
  aewe = a->w - patch_w;
  aehe = a->h - patch_w;
  bewe = b->w - patch_w;
  behe = b->h - patch_w; 
  if (rotation == 90){
    aews = patch_w;
    aehs = 0;
    aewe = a->w;
    aehe = a->h - patch_w;

    bews = patch_w;
    behs = 0;
    bewe = b->w;
    behe = b->h - patch_w;
  }
  else if (rotation == 180){
    aews = patch_w;
    aehs = patch_w;
    aewe = a->w;
    aehe = a->h;

    bews = patch_w;
    behs = patch_w;
    bewe = b->w;
    behe = b->h;
  }
  else if (rotation == 270){
    aews = 0;
    aehs = patch_w;
    aewe = a->w - patch_w;
    aehe = a->h;

    bews = 0;
    behs = patch_w;
    bewe = b->w - patch_w;
    behe = b->h;
  }

  memset(ann->data, 0, sizeof(int)*a->w*a->h);
  memset(annd->data, 0, sizeof(int)*a->w*a->h);
  for (int ay = aehs; ay < aehe; ay++) {
    for (int ax = aews; ax < aewe; ax++) {
      int bx = bews + rand()%(bewe-bews);
      int by = behs + rand()%(behe-behs);
      (*ann)[ay][ax] = XY_TO_INT(bx, by);
      (*annd)[ay][ax] = dist(a, b, ax, ay, bx, by);
    }
  }

  
  for (int iter = 0; iter < pm_iters; iter++) {
    /* In each iteration, improve the NNF, by looping in scanline or reverse-scanline order. */
    int ystart = aehs, yend = aehe, ychange = 1;
    int xstart = aews, xend = aewe, xchange = 1;
    if (iter % 2 == 1) {
      xstart = xend-1; xend = aews-1; xchange = -1;
      ystart = yend-1; yend = aehs-1; ychange = -1;
    }

    for (int ay = ystart; ay != yend; ay = ay + ychange) {
      // #pragma omp parallel for
      for (int ax = xstart; ax != xend; ax += xchange) { 
        /* Current (best) guess. */
        int v = (*ann)[ay][ax];
        int xbest = INT_TO_X(v), ybest = INT_TO_Y(v);
        int dbest = (*annd)[ay][ax];

        /* Propagation: Improve current guess by trying instead correspondences from left and above (below and right on odd iterations). */
        if ((unsigned) (ax - xchange) < (unsigned) aewe) {
          int vp = (*ann)[ay][ax-xchange];
          int xp = INT_TO_X(vp) + xchange, yp = INT_TO_Y(vp);
          if ((unsigned) xp < (unsigned) bewe && (unsigned) xp >= (unsigned) bews) {
            improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp);
          }
        }

        if ((unsigned) (ay - ychange) < (unsigned) aehe) {
          int vp = (*ann)[ay-ychange][ax];
          int xp = INT_TO_X(vp), yp = INT_TO_Y(vp) + ychange;
          if ((unsigned) yp < (unsigned) behe && (unsigned) yp >= (unsigned) behs) {
            improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp);
          }
        }

        /* Random search: Improve current guess by searching in boxes of exponentially decreasing size around the current best guess. */
        int rs_start = rs_max;
        if (rs_start > MAX(b->w, b->h)) { rs_start = MAX(b->w, b->h); }
        for (int mag = rs_start; mag >= 1; mag /= 2) {
          /* Sampling window */
          int xmin = MAX(xbest-mag, bews), xmax = MIN(xbest+mag+1,bewe);
          int ymin = MAX(ybest-mag, behs), ymax = MIN(ybest+mag+1,behe);
          int xp = xmin + rand()%(xmax-xmin);
          int yp = ymin + rand()%(ymax-ymin);
          improve_guess(a, b, ax, ay, xbest, ybest, dbest, xp, yp);
        }

        (*ann)[ay][ax] = XY_TO_INT(xbest, ybest);
        (*annd)[ay][ax] = dbest;
      }
    }
  }
}


int main(int argc, char *argv[]) {
  argc--;
  argv++;
  if (argc != 4) { fprintf(stderr, "pm_minimal a b ann annd\n"
                                   "Given input images a, b outputs nearest neighbor field 'ann' mapping a => b coords, and the squared L2 distance 'annd'\n"
                                   "These are stored as RGB 24-bit images, with a 24-bit int at every pixel. For the NNF we store (by<<12)|bx."); exit(1); }
  printf("Loading input images\n");
  BITMAP *a = load_bitmap(argv[0]);
  BITMAP *b = load_bitmap(argv[1]);

  BITMAP *ann = NULL, *annd = NULL;
  printf("Running PatchMatch\n");

  clock_t start_time = clock();
  patchmatch(a, b, ann, annd);
  start_time = clock() - start_time;
  printf("patchmatch uses %f seconds\n", ((float)start_time)/CLOCKS_PER_SEC);
  printf("Saving output images\n");
  save_bitmap(ann, argv[2]);
  save_bitmap(annd, argv[3]);
  return 0;
}