---
name: cs2-kit
description: Use the locally installed CS2 building kit to create or refine Cities Skylines II building assets from photos, scans, or Blender references. Use for the kit's photo comparison, geometry generation, LOD, and FBX workflow.
---

# CS2 building kit

The kit root is `C:/Users/sims/Desktop/CitiesSimulator/cs2-kit`. Execute its commands with that working directory; paths in the upstream Claude skills assume the kit root. Read its `README.md`, `AGENTS.md`, and relevant files in `docs/agent/` for the task. Claude-specific hooks and slash commands are not Codex features; use the documented Python commands directly.

Create a separate kit project with `python tools/project.py new <name>` (or `--template generic` for irregular volumes), and run `python tools/agent.py doctor --project <name> --json`. Preserve existing work and reference images. Choose inputs based on evidence: multiple clear photos for facade, and scan/VR metadata when available for footprint. Mark missing dimensions and unseen geometry as estimates; do not treat a scan made from an approximation as evidence of the real building. Compare actual rendered results to references. Follow applicable quick, visual, and final checks and report exact results, including unavailable or failed checks.

The kit produces CS2 FBX assets; integration into other renderers or GLB workflows requires separate verification. Follow the user's requested asset naming and use over repository defaults where they conflict. Do not assume the kit automatically produces accurate or photorealistic geometry.
