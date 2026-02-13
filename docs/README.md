# Spaghetti Bench Website

This directory contains the static site for Spaghetti Bench, deployed via GitHub Pages.

## How it works

- Static HTML/CSS/JS files are served from this directory
- Trace JSON files are lazy-loaded from the `results/` directory via GitHub raw URLs
- This keeps the docs/ folder lightweight (~1MB)

## Local Development

To test locally:
```bash
cd docs
python3 -m http.server 8000
```

Then visit http://localhost:8000

Note: Trace loading will fail locally. To test with traces, either:
1. Run the full Python server from viz/serve_traces.py
2. Or update TRACES_SOURCE in trace_visualizer.html to 'local'
