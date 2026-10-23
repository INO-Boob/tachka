# Attribution and media provenance

- Concept, art direction, interaction design and After Effects finishing: Amir Mušić.
- Website implementation: developed with coding-agent assistance; application code published under MIT.
- **This fork (911 edition):** every image and video in `public/media` that the page uses was re-rendered in Blender (Cycles) from the free 3D model "Free Porsche 911 Carrera 4S" downloaded from Sketchfab (file dated 2020-11-24). Keep the model author's credit and check the license on its Sketchfab page before publishing or redistributing these renders. The Porsche crest was removed and the number plates replaced with VEYRA plates. The studio, materials, electric drive unit, battery pack, aero covers, X-ray scan and hood motion were built by the render scripts in `tools/render-911/`. Porsche and 911 are trademarks of Dr. Ing. h.c. F. Porsche AG; this independent concept is not affiliated with or endorsed by Porsche.
- Original v1.0.0 concept stills and appearance variants (replaced in this fork, still in Git history): AI-generated imagery produced with OpenAI image generation/editing.
- Original v1.0.0 hover films (replaced in this fork, still in Git history): Kling 3.0 image-to-video via Pika, followed by Amir's After Effects time remapping and forward/reverse exports.
- LTX API examples: optional workflows for future assets, not provenance claims about the bundled films. No LTX, Kling or Pika model weights or SDK code are redistributed.

The author offers the bundled concept images, video exports and project screenshots under the MIT license to the extent of the author's rights in them. This grants no rights to third-party trademarks or likenesses and makes no claim of exclusive ownership of AI-generated material. No provider endorsement is implied.

Space Grotesk is loaded from Google Fonts and is not bundled in this release. Its font software is distributed upstream under the SIL Open Font License; preserve the upstream license if you choose to self-host it. See the [upstream font repository](https://github.com/floriankarsten/space-grotesk).

React, TypeScript, Vite, Tailwind CSS, PostCSS, Autoprefixer and Lucide retain their respective upstream licenses. Dependency packages include their own license files. Lucide uses the ISC license. This repository's MIT license does not replace dependency licenses.
