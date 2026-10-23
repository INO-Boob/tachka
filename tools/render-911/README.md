# 911 render pipeline

Rebuilds every page image and hover video from the Sketchfab model "Free Porsche 911 Carrera 4S".
The model is not committed; download it yourself and keep its author credit and license.

```sh
python3 -m venv .venv && .venv/bin/pip install bpy pillow numpy   # Blender 5.2 as a Python module
cd tools/render-911
../../.venv/bin/python -I studio.py /path/to/model.blend jobs.json    # ~45 min on 4 CPU cores
../../.venv/bin/python -I build_media.py final ../../public/media     # needs ffmpeg
```

- `studio.py` builds the studio (lights, car paint, shadow catcher), splits the front lid off the body
  on a hinge, adds the electric drive unit, battery pack and aero covers, then renders each job as RGBA.
  It also writes `final/points.json`: hotspot and annotation positions projected from 3D, in percent.
- `build_media.py` puts the renders on the studio backdrop, writes the stills and encodes the four
  60fps hover clips. Hood frames are rendered only inside a border region and blended into the
  neutral still, so the first hover frame is exactly `exterior-polished.png`.
- `compose.py` is the shared backdrop.
