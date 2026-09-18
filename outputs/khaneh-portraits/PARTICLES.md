# Particle sculpture

Open Hamid's portrait and choose **Particles** or **White statue**. The point study uses a white background, monochrome circular dots, a density slider, gentle motion, and mouse/touch/keyboard rotation. Pause motion freezes the animation. Reduced-motion preferences start it paused.

`particles.js` draws points with WebGL vertex and fragment shaders, inspired by the circular point rendering in [Electron Simulation](https://github.com/parniayzdin/Electron_Simulation). This is browser graphics, not CUDA or a backend rendering job. Hardware acceleration depends on the browser and its graphics configuration.

The separate `assets/sculpture/hamid-particles.json` contains 48,000 sampled points. Larger forms receive surface samples; an exponentially thinning outer population provides a soft drifting edge. Fine eyebrow, eyelid, lip, nose, hair-lock, lace, and seam components are omitted. This remains an artistic pose study, not an authenticated likeness.

To regenerate from the existing GLB, run from the repository root:

```sh
blender --background --python scripts/sample_sculpture_particles.py
```

The script reads the GLB and writes only the particle JSON. It never saves over the original `.blend` or `.glb`. The original statue viewer is retained. No new packages or backend service are required.

Rendering stops when the dialog is closed, the white statue is selected, or the browser tab is hidden. A graphics failure shows a message directing visitors to the original statue.
