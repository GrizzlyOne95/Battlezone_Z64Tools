# Battlezone 64 Binary Model Format Notes

Last updated: 2026-02-24

This file captures the current reverse-engineered model format behavior used by `tools/bz64_extract.py`.

## Core Signature
- Model stream signature: `D700000280008000`
- Typical model blob starts at display-list offset `0x08`.

## Display List Semantics Used
- Command words are 8-byte pairs (`w0`, `w1`) in big-endian.
- Implemented opcodes:
1. `0x01` (`VTX`)
2. `0x05` (`TRI1`)
3. `0x06` (`TRI2`)
4. `0x07` (`G_QUAD`, best-effort)
5. `0xDA` (`G_MTX`)
6. `0xD8` (`POPMTX`, best-effort)
7. `0xDB` (`G_MOVEWORD`, segment base tracking)
8. `0xDE` (`G_DL`)
9. `0xDF` (`EndDL`)
10. `0xFD` (`G_SETTIMG`)
11. `0xF5` (`G_SETTILE`)
12. `0xF2` (`G_SETTILESIZE`)
13. `0xF0` (`G_LOADTLUT`)
14. `0xF3` (`G_LOADBLOCK`)
15. `0xD7` (`G_TEXTURE`, UV scale tracking)
16. `0xBE` (`G_CULLDL`, ignored)

### `VTX` decode (F3DEX2-like)
- `n = (w0 >> 12) & 0xFF`
- `end = (w0 & 0x0FFF) >> 1`
- `v0 = end - n`
- Vertex source address comes from `w1`, and segment `0x08` is currently accepted.
- Segment base updates via `G_MOVEWORD` (G_MW_SEGMENT) are now tracked when present.
- Parsed vertex stride is 16 bytes:
1. `x,y,z` signed 16-bit
2. `s,t` signed 16-bit
3. `rgba` as 8-bit channels

### `TRI1` decode
- Vertex indices are taken from low bytes of `w0`, divided by 2 (`//2`) to map to cache slots.

## Vertex Cache / Mesh Build
- Parser uses an RSP-like vertex cache (64 slots for safety).
- Faces are emitted from resolved cache slots.
- Final mesh compacts to only referenced vertices.
- UV output uses per-triangle scale from `G_TEXTURE` and tile shift from `G_SETTILE`.
- Effective baseline divisor for common `G_TEXTURE` scale `0x8000` is `2048` (not `4096`).
- `G_SETTILESIZE` contributes UV origin offset (`uls/ult` -> 5-bit fractional vertex units).
- Active render tile is taken from `G_TEXTURE` tile field (not inferred only from non-7 `G_SETTILE` traffic).

## Current Quality Checks
- Mesh must have at least 1 triangle and 3 vertices.
- Degenerate-triangle ratio must be <= 5%.
- Bounding extents must be non-collapsed and not absurdly large.
- Optional strict mode (`--strict-mesh`) adds anti-spaghetti checks:
  - rejects meshes with excessive very-long edge ratio
  - rejects extreme axis-stretch outliers

## Texture Extraction (Current Assumption)
- Texture decode now prefers DL-driven state (palette/image + tile size).
- Load-vs-render tile tracking plus `G_LOADTLUT` / `G_LOADBLOCK` hints improve palette and size inference.
- `G_LOADBLOCK` texel counts are converted from load-size to render-size before width/height guessing.
  - This fixed CI4 cases where data was loaded as 16b then rendered as 4b (e.g., Y297 `mat02` path).
- Fixed CI4 layout fallback (legacy):
1. TLUT at `0x0BA0`
2. CI4 pixels at `0x0BC0`
3. Size `32x32`
- Small model blobs can still fail texture extraction if no valid DL state is present.

## OBJ/MTL Export Behavior
- Multi-material OBJ export is per-triangle (`usemtl` switches in face stream).
- Material names are now model-stem scoped to avoid Blender collisions across imports.
  - Format: `<model_stem>_matXX`
- Texture files are written per decoded state:
  - Format: `<model_stem>_texXX.png`

## 2026-02-24 Validation Notes (Y297 Refinement)
- Target: `extract_out/tmp_y297.bin` -> `tmp_y297_fix7.obj/.mtl`
- Confirmed fixes:
1. Correct per-face material assignment with unique material names.
2. UV scaling corrected for previously underscaled faces (`mat06` class issue).
3. Overscaled UV regression corrected by using `G_TEXTURE` scale/shift path consistently.
4. Wrong-texture case corrected by `G_LOADBLOCK` load-size/render-size texel conversion (`mat02`).
- Result: `tmp_y297_fix7` matches expected in Blender except for normal N64 repeat/clamp differences.

## Reference Ground Truth Binaries
- `9F41DA.bin`: `tri=360`, `vert=352`
- `9F347C.bin`: `tri=224`, `vert=240`
- `9F64EA.bin`: `tri=360`, `vert=391`
- Reference mapping artifact:
  - `extract_out/models_yay0_focus_v1/reference_matches.json`

## Validation Across Curated `models/` Set
- Input set: `models/*.bin` (`206` files)
- Parse success: `206/206`
- Mesh quality pass: `166/206`
- Texture decode pass (fixed CI4 assumption): `178/206`
- Report artifacts:
  - `extract_out/models_reference_check.json`
  - `extract_out/models_reference_check.md`

## ROM Extraction Results Using Current Knowledge
- Raw ROM signature extraction:
  - Command: `python tools\bz64_extract.py batch-models --rom "Battlezone - Rise of the Black Dogs (USA).z64" --outdir extract_out\models_romscan_v1 --texture`
  - Exported: `182`
- Yay0 extraction (all signatures, low tri threshold):
  - Command: `python tools\bz64_extract.py batch-models-yay0 --rom "Battlezone - Rise of the Black Dogs (USA).z64" --outdir extract_out\models_yay0_focus_v2 --texture --all-signatures --min-tris 1`
  - Exported: `299`
- Blender-ready extraction profile:
  - Command: `python tools\bz64_extract.py batch-models-yay0 --rom "Battlezone - Rise of the Black Dogs (USA).z64" --outdir extract_out\models_yay0_blender_v2 --texture --min-tris 24 --strict-mesh`
  - Exported: `44`
- Combined summary artifact:
  - `extract_out/model_extraction_summary_v2.json`

## Known Gaps
- Texture decoding is DL-state-driven for current model paths, but TMEM line/tmem-offset emulation is still incomplete.
- Some parsed blobs with very small triangle counts are likely effects/helpers, not gameplay-visible meshes.
- Some larger model-like binaries still produce weak geometry and may use variant DL conventions not yet decoded.
