import http.server
import socketserver
import webbrowser
import threading
import time

PORT = 8000
DIRECTORY = '.'

class DashboardServer:
    def __init__(self):
        self.httpd = None
        self.server_thread = None
        self.is_running = False
    
    def start_server(self):
        if self.is_running:
            print("Dashboard server is already running")
            return
        
        try:
            Handler = http.server.SimpleHTTPRequestHandler
            self.httpd = socketserver.TCPServer(("", PORT), Handler)
            self.is_running = True
            print(f"Dashboard server started on port {PORT}")
            self.httpd.serve_forever()
        except OSError as e:
            if e.errno == 48:  # Address already in use
                print(f"Port {PORT} is already in use")
            else:
                print(f"Failed to start server: {e}")
            self.is_running = False
        except Exception as e:
            print(f"Server error: {e}")
            self.is_running = False
    
    def open_browser(self):
        time.sleep(1)
        webbrowser.open(f"http://localhost:{PORT}/docs")
    
    def start_dashboard(self):
        if self.is_running:
            self.open_browser()
            return
        
        # print("Starting dashboard server...")
        try:
            # Start server in daemon thread so it closes when main app closes
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()
            
            browser_thread = threading.Thread(target=self.open_browser, daemon=True)
            browser_thread.start()
            
        except Exception as e:
            print(f"Failed to start dashboard: {e}")
    
    def stop_server(self):
        """Stop the dashboard server."""
        if self.httpd and self.is_running:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.is_running = False
            # print("Dashboard server stopped")

# Global server instance
_dashboard_server = DashboardServer()

def start_dashboard():
    _dashboard_server.start_dashboard()

def stop_dashboard():
    _dashboard_server.stop_server()

def is_dashboard_running():
    return _dashboard_server.is_running

# Legacy function for backward compatibility
def dashboard_run():
    start_dashboard()