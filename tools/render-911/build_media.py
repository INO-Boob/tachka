"""Turn the raw RGBA renders into the site's media set.

Usage: build_media.py <final dir> <public/media dir>
"""
import sys, os, subprocess, shutil, json
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from compose import backdrop

final, media = sys.argv[1], sys.argv[2]
work = os.path.join(final, 'frames'); os.makedirs(work, exist_ok=True)

def flat(path):
    im = Image.open(path).convert('RGBA'); bg = backdrop(*im.size).convert('RGBA'); bg.alpha_composite(im)
    return np.asarray(bg.convert('RGB')).astype(np.float32)

def save(arr, path, **kw):
    Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8)).save(path, **kw)

# Region mask for the hood frames: feathered inside the render border.
border = [0.04, 0.24, 0.64, 1.0]
base = flat(f'{final}/neutral.png'); H, W, _ = base.shape
mask = Image.new('L', (W, H), 0)
x0, x1 = int(border[0] * W) + 28, int(border[2] * W) - 28
y0, y1 = int((1 - border[3]) * H) + 28, int((1 - border[1]) * H) - 28
mask.paste(255, (x0, y0, x1, y1)); mask = np.asarray(mask.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)[..., None] / 255

hood_files = sorted(f for f in os.listdir(f'{final}/hood') if f.endswith('.png'))
hood = []
for f in hood_files:
    hood.append(base * (1 - mask) + flat(f'{final}/hood/{f}') * mask)
neutral = hood[0]  # the still is exactly the first hover frame
save(neutral, f'{media}/exterior-polished.png', optimize=True)

def variant(name, out):
    # Appearance renders share the neutral composition; reuse the neutral hood region
    # only for the base image, variants are complete renders.
    save(flat(f'{final}/{name}.png'), f'{media}/{out}', optimize=True)
os.makedirs(f'{media}/config', exist_ok=True)
for src, dst in [('paint-electric', 'config/electric-green.png'), ('paint-lime', 'config/lime-green.png'),
                 ('paint-sky', 'config/sky-blue.png'), ('paint-graphite', 'config/graphite.png'),
                 ('wheels-aero', 'config/wheels-aero.png'), ('wheels-forged', 'config/wheels-forged.png')]:
    variant(src, dst)
def detail(name, out):
    # The detail copy sits over the right of the frame: fade the car back into the
    # empty studio there so the text stays readable.
    img = flat(f'{final}/{name}.png'); bg = np.asarray(backdrop(W, H)).astype(np.float32)
    t = np.clip((np.linspace(0, 1, W) - 0.55) / 0.17, 0, 1); r = (t * t * (3 - 2 * t) * 0.93)[None, :, None]
    save(img * (1 - r) + bg * r, f'{media}/{out}', optimize=True)
detail('drive-detail', 'drive-blue.png')
detail('battery-detail', 'battery-blue.png')

# Battery reveal: an X-ray scan sweeps from the nose to the tail with a thin electric-green edge.
xray = flat(f'{final}/xray.png')
alpha = np.asarray(Image.open(f'{final}/neutral.png').split()[-1]).astype(np.float32) / 255
car_cols = np.where(alpha.max(0) > 0.5)[0]; cx0, cx1 = car_cols.min() - 20, car_cols.max() + 20
xs = np.arange(W)[None, :, None].astype(np.float32)
acid = np.array([0xed, 0xff, 0x39], np.float32)
# The scan line only lights the car itself: where the body and its X-ray differ.
body = (np.abs(xray - neutral).sum(-1) > 18).astype(np.float32) * (alpha > 0.95)
body = (np.asarray(Image.fromarray((body * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255)[..., None]
def ease(t): return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def scan(t):
    edge = cx0 + (cx1 - cx0 + 120) * t - 60
    m = np.clip((edge - xs) / 60 + 0.5, 0, 1)
    line = np.exp(-((xs - edge) / 7) ** 2) * (0 < t < 1) * body
    out = neutral * (1 - m) + xray * m
    return out + (acid - out) * line * 0.75
battery = [scan(ease(i / 59)) for i in range(60)]
battery[0] = neutral; battery[-1] = xray

def encode(frames, path):
    d = os.path.join(work, os.path.basename(path)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for i, fr in enumerate(frames): save(fr[:H - (H % 2)], f'{d}/{i:03d}.png', compress_level=1)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', '60', '-i', f'{d}/%03d.png', '-c:v', 'libx264',
                    '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', path], check=True)
    shutil.rmtree(d)

# Hold a few frames at each end so decoders land cleanly on the endpoint pose.
hold = lambda fs: [fs[0]] * 2 + fs + [fs[-1]] * 4
encode(hold(hood), f'{media}/hood-hover-forward.mp4')
encode(hold(hood[::-1]), f'{media}/hood-hover-reverse.mp4')
encode(hold(battery), f'{media}/battery-hover-forward.mp4')
encode(hold(battery[::-1]), f'{media}/battery-hover-reverse.mp4')
print('done')
