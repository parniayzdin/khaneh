# Khaneh — an atlas of remembrance

A local frontend preview: six sourced portraits connected to four cities on an illustrated Iran map. Hamid Mahdavi's portrait opens an interactive white sculpture room. Other portraits open their sourced stories.

## Preview

Run from the project root:

    node work/khaneh-preview-server.cjs

Visit http://127.0.0.1:4173. The preview server is bound to this computer only. Use the HTTP preview for the 3D module rather than opening the HTML as a file.

## Hamid's sculpture

- Click Hamid's portrait in either the atlas or portrait gallery.
- The entrance moves closer to the statue; drag to turn, scroll/pinch to zoom, or use the controls. Reset view restores the reference angle.
- Escape or Return to the atlas closes the room and restores focus to the portrait.
- The figure, clothing, and pedestal are unpainted white. It is an artistic interpretation of the supplied pose, not a verified reconstruction or a claimed exact likeness.
- Model: assets/sculpture/hamid-carrying-white.glb
- Editable source: assets/sculpture/hamid-carrying-white.blend
- Rendered study: assets/sculpture/hamid-carrying-white.png
- Build script: work/build_hamid_sculpture.py under the project root.

## Files and credits

Main frontend: atlas.html (mirrored in index.html and index-updated.html), atlas.css, persian-theme.css, atlas.js, sculpture.css, sculpture.js, assets/data.js. No frontend build step or backend database.

The interactive viewer uses the locally bundled Google model-viewer 4.3.1, Apache-2.0; its license is stored in assets/vendor. WebGL is required. Sculpture and art assets are local. Google Fonts needs a connection and has standard font fallbacks.

Story sources and portrait credits accompany every record. Museum artwork credits are in Sources & artwork. The three additional Persian miniature images were supplied by the user; their original attribution is to be confirmed. Portrait reproduction rights remain with their owners. This is a private design preview.

The outline is generalized Natural Earth data. Pins indicate approximate city centers, not exact death locations. Earlier frontend files are preserved under work/khaneh-before-sculpture and work/khaneh-before-redesign in the project root.
