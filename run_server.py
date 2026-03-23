import http.server
import socketserver
import os
import json
import subprocess

PORT = 8080
DIRECTORY = "Interactive_Report"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Allow CORS and disable caching
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_POST(self):
        if self.path == '/api/run_sim':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                params = json.loads(post_data.decode('utf-8'))
                # Save params.json for the Python scripts to read
                with open(os.path.join(DIRECTORY, 'params.json'), 'w') as f:
                    json.dump(params, f, indent=2)
                
                print(f"\n--- Running backend simulation with new params ---")
                
                # Execute pipeline sequentially
                scripts = [
                    'Global_LP.py',
                    'Shift_Scheduler.py',
                    'Simulation_Fixed_Schedule.py',
                    'Generate_Report_Data.py'
                ]
                
                for script in scripts:
                    print(f"Executing {script}...")
                    subprocess.run(["python", script], check=True, cwd=os.getcwd())
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
                print("--- Backend simulation completed successfully ---\n")
                
            except Exception as e:
                print(f"Error during simulation: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    # Change into the directory of this script to ensure reliable relative paths
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory '{DIRECTORY}' not found.")
        exit(1)
        
    # Set up the server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving '{DIRECTORY}' API and static files at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
