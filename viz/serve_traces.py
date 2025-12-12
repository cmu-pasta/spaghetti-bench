#!/usr/bin/env python3
"""
Simple HTTP server to view agent traces.
Serves the trace visualizer and provides API endpoints to browse traces.
"""

import http.server
import socketserver
import json
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import mimetypes

PORT = 8001
# Use absolute path resolution to avoid issues with working directory changes
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results"
VISUALIZER_PATH = SCRIPT_DIR / "trace_visualizer.html"


class TraceServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        print(f"[REQUEST] {self.command} {path}")

        # Serve the main visualizer page
        if path == "/" or path == "/index.html":
            self.serve_visualizer()
            return

        # API endpoint to list all traces
        if path == "/api/traces":
            self.list_traces()
            return

        # API endpoint to get a specific trace
        if path.startswith("/api/trace/"):
            trace_path = path[len("/api/trace/"):]
            self.serve_trace(trace_path)
            return

        # API endpoint to get a patch file
        if path.startswith("/api/patch/"):
            patch_path = path[len("/api/patch/"):]
            self.serve_patch(patch_path)
            return

        # Serve static files
        print(f"[REQUEST] Falling through to static file handler for: {path}")
        super().do_GET()

    def serve_visualizer(self):
        """Serve the trace visualizer HTML with API support."""
        try:
            with open(VISUALIZER_PATH, 'r', encoding='utf-8') as f:
                content = f.read()

            # Inject script to auto-load traces from API
            inject_script = """
    <script>
        let fileMetadata = new Map(); // Track file paths and their modification times
        let pollInterval = null;

        // Auto-load traces from API on page load
        window.addEventListener('DOMContentLoaded', () => {
            loadTracesFromAPI();
            // Start polling for changes every 2 seconds
            pollInterval = setInterval(checkForUpdates, 2000);
        });

        async function loadTracesFromAPI() {
            try {
                if (typeof setLoadingStatus === 'function') setLoadingStatus(true);

                console.log('Fetching traces from /api/traces...');
                const response = await fetch('/api/traces');
                console.log('Response status:', response.status);
                const traceFiles = await response.json();
                console.log('Found', traceFiles.length, 'trace files');

                if (traceFiles.length === 0) {
                    if (typeof setLoadingStatus === 'function') setLoadingStatus(false);
                    return;
                }

                // Track file metadata
                fileMetadata.clear();
                traceFiles.forEach(file => {
                    fileMetadata.set(file.path, {
                        modified: file.modified,
                        size: file.size
                    });
                });

                console.log('Loading individual trace files...');
                const loadedTraces = await Promise.all(
                    traceFiles.map(async (file, index) => {
                        console.log(`Loading ${index + 1}/${traceFiles.length}: ${file.path}`);
                        const res = await fetch(`/api/trace/${encodeURIComponent(file.path)}`);
                        const trace = await res.json();
                        trace._filename = file.name;
                        trace._path = file.path;
                        trace._modified = file.modified;
                        return trace;
                    })
                );

                console.log('Successfully loaded', loadedTraces.length, 'traces');
                traces = loadedTraces;
                renderTraceList();

                // Check if there's a trace specified in the URL hash
                if (window.location.hash.startsWith('#trace/')) {
                    if (typeof loadTraceFromUrl === 'function') {
                        loadTraceFromUrl();
                    }
                } else if (traces.length > 0 && !currentTrace) {
                    console.log('Selecting first trace');
                    selectTrace(0);
                }

                if (typeof setLoadingStatus === 'function') setLoadingStatus(false);
            } catch (error) {
                console.error('Error loading traces from API:', error);
                if (typeof setLoadingStatus === 'function') setLoadingStatus(false);
            }
        }

        async function checkForUpdates() {
            try {
                const response = await fetch('/api/traces');
                const traceFiles = await response.json();

                let hasChanges = false;
                const newPaths = new Set(traceFiles.map(f => f.path));
                const oldPaths = new Set(fileMetadata.keys());

                // Check for new or modified files
                for (const file of traceFiles) {
                    const oldMeta = fileMetadata.get(file.path);
                    if (!oldMeta || oldMeta.modified !== file.modified) {
                        hasChanges = true;
                        break;
                    }
                }

                // Check for deleted files
                for (const path of oldPaths) {
                    if (!newPaths.has(path)) {
                        hasChanges = true;
                        break;
                    }
                }

                if (hasChanges) {
                    console.log('Detected changes, reloading traces...');
                    const currentPath = currentTrace?._path;
                    await loadTracesFromAPI();

                    // Try to restore the current trace selection
                    if (currentPath) {
                        const index = traces.findIndex(t => t._path === currentPath);
                        if (index >= 0) {
                            selectTrace(index);
                        }
                    }
                }
            } catch (error) {
                console.error('Error checking for updates:', error);
            }
        }
    </script>
"""

            # Inject before closing body tag
            content = content.replace('</body>', f'{inject_script}</body>')

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error serving visualizer: {str(e)}")

    def list_traces(self):
        """List all trace JSON files in the results directory."""
        try:
            traces = []

            print(f"[API] Listing traces from: {RESULTS_DIR}")
            print(f"[API] Directory exists: {RESULTS_DIR.exists()}")

            if RESULTS_DIR.exists():
                for json_file in RESULTS_DIR.rglob("*.json"):
                    rel_path = json_file.relative_to(RESULTS_DIR)
                    stat = json_file.stat()
                    traces.append({
                        "name": json_file.name,
                        "path": str(rel_path),
                        "full_path": str(json_file),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })

            # Sort by path
            traces.sort(key=lambda x: x['path'])
            print(f"[API] Found {len(traces)} trace files")

            response = json.dumps(traces, indent=2)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response.encode('utf-8')))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error listing traces: {str(e)}")

    def serve_trace(self, trace_path):
        """Serve a specific trace JSON file."""
        try:
            # URL-decode the path (e.g., %2F becomes /)
            decoded_path = unquote(trace_path)
            full_path = RESULTS_DIR / decoded_path
            print(f"[API] Serving trace: {trace_path} -> {decoded_path} -> {full_path}")

            # Security check: ensure the path is within RESULTS_DIR
            if not str(full_path.resolve()).startswith(str(RESULTS_DIR.resolve())):
                print(f"[API] Access denied for: {full_path}")
                self.send_error(403, "Access denied")
                return

            if not full_path.exists():
                print(f"[API] Trace not found: {full_path}")
                self.send_error(404, "Trace not found")
                return

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error serving trace: {str(e)}")

    def serve_patch(self, patch_path):
        """Serve a patch file corresponding to a trace."""
        try:
            print(f"[API] serve_patch called with: {patch_path}")

            # URL-decode the path and change .json to .patch
            decoded_path = unquote(patch_path)
            print(f"[API] After URL decode: {decoded_path}")

            if decoded_path.endswith('.json'):
                decoded_path = decoded_path[:-5] + '.patch'
                print(f"[API] Changed .json to .patch: {decoded_path}")

            full_path = RESULTS_DIR / decoded_path
            print(f"[API] Serving patch: {patch_path} -> {decoded_path} -> {full_path}")
            print(f"[API] Full path exists: {full_path.exists()}")
            print(f"[API] Full path resolved: {full_path.resolve()}")
            print(f"[API] RESULTS_DIR: {RESULTS_DIR.resolve()}")

            # Security check: ensure the path is within RESULTS_DIR
            if not str(full_path.resolve()).startswith(str(RESULTS_DIR.resolve())):
                print(f"[API] Access denied for: {full_path}")
                self.send_error(403, "Access denied")
                return

            if not full_path.exists():
                print(f"[API] Patch not found: {full_path}")
                # Return empty response instead of 404 so UI can handle gracefully
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.send_header('Content-Length', 0)
                self.end_headers()
                return

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error serving patch: {str(e)}")

    def log_message(self, format, *args):
        """Custom log message format."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """Start the trace visualization server."""
    if not VISUALIZER_PATH.exists():
        print(f"Error: Visualizer HTML not found at {VISUALIZER_PATH}")
        return 1

    if not RESULTS_DIR.exists():
        print(f"Warning: Results directory not found at {RESULTS_DIR}")
        print("Creating empty results directory...")
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Change to the script directory
    os.chdir(Path(__file__).parent)

    # Enable socket reuse to avoid "address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), TraceServerHandler) as httpd:
        print(f"╔═══════════════════════════════════════════════════════════╗")
        print(f"║  Agent Trace Visualizer Server                           ║")
        print(f"╠═══════════════════════════════════════════════════════════╣")
        print(f"║  Server running at: http://localhost:{PORT}               ║")
        print(f"║  Results directory: {RESULTS_DIR}                        ")
        print(f"║  Trace files found: {len(list(RESULTS_DIR.rglob('*.json')) if RESULTS_DIR.exists() else [])}                                    ")
        print(f"║  Press Ctrl+C to stop the server                         ║")
        print(f"╚═══════════════════════════════════════════════════════════╝")
        print()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            return 0


if __name__ == "__main__":
    exit(main())
