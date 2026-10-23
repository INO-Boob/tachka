"""Composite RGBA renders over the VEYRA studio backdrop. Usage: compose.py out.png in.png [in2.png ...]"""
import sys, numpy as np
from PIL import Image
def backdrop(w, h):
    y = np.linspace(0, 1, h)[:, None]; x = np.linspace(-1, 1, w)[None, :]
    top = np.array([0x5c, 0x7a, 0x92]); mid = np.array([0x6c, 0x89, 0xa0]); low = np.array([0x86, 0xa2, 0xb8])
    t = np.clip((y - 0.15) / 0.6, 0, 1)[..., None]
    col = top * (1 - t) + mid * t
    floor = np.clip((y - 0.62) / 0.38, 0, 1)[..., None]
    col = col * (1 - floor * 0.7) + low * floor * 0.7
    glow = np.exp(-((x * 0.9) ** 2 + ((y - 0.55) * 2.2) ** 2))[..., None]
    col = col + glow * 10 - (np.abs(x) ** 3)[..., None] * 8
    rng = np.random.default_rng(3); col = col + rng.normal(0, 0.9, col.shape)  # fine grain avoids banding
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), 'RGB')
if __name__ == '__main__':
  out, *ins = sys.argv[1:]
  for i, src in enumerate(ins):
    im = Image.open(src).convert('RGBA')
    bg = backdrop(*im.size).convert('RGBA'); bg.alpha_composite(im)
    bg.convert('RGB').save(out if len(ins) == 1 else out.replace('%', str(i)), optimize=True)
