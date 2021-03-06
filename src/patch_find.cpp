
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
    for (int dx = dxstart; dx < dxend; dx++) {
      int ac = arow[dx];
      int bc = brow[dx];
      int dr = (ac&255)-(bc&255);
      int dg = ((ac>>8)&255)-((bc>>8)&255);
      int db = (ac>>16)-(bc>>16);
      ans += dr*dr + dg*dg + db*db;
    }
    if (ans >= cutoff) { return cutoff; }
  }
  return ans;
}

/* Match image a to image b, returning the nearest neighbor field mapping a => b coords, stored in an RGB 24-bit image as (by<<12)|bx. */
void patchmatch(BITMAP *a, BITMAP *b, BITMAP *&ann, BITMAP *&annd, int rot = 0) {
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

      int minDis = INT_MAX;
      for (int by = behs; by < behe; by++){
        for (int bx = bews; bx < bewe; bx++) {
          int dis = dist(a, b, ax, ay, bx, by);
          if(minDis < (*annd)[ay][ax]){
            (*ann)[ay][ax] = XY_TO_INT(bx, by);
            (*annd)[ay][ax] = dis;
          }
        }
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
  printf("Running PatchMatch BruteForced\n");

  clock_t start_time = clock();
  patchmatch(a, b, ann, annd);
  start_time = clock() - start_time;
  printf("patchmatch uses %f seconds\n", ((float)start_time)/CLOCKS_PER_SEC);
  printf("Saving output images\n");
  save_bitmap(ann, argv[2]);
  save_bitmap(annd, argv[3]);
  return 0;
}