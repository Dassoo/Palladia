import http.server
import socketserver
import webbrowser
import threading
import atexit
import errno
from functools import partial


PORT = 8000
DIRECTORY = '.'

# HTTP handler that suppresses broken pipe errors
class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = DIRECTORY
        super().__init__(*args, directory=directory, **kwargs)
    
    def log_message(self, format, *args):
        # Suppress access log messages
        pass
    
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            # Client disconnected, ignore these errors
            pass
        except OSError as e:
            if e.errno == errno.EPIPE:
                # Broken pipe, ignore
                pass
            else:
                raise

# TCP Server with address reuse
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

class DashboardServer:
    def __init__(self):
        self.httpd = None
        self.server_thread = None
        self.is_running = False

    def _run_server(self):
        if self.is_running:
            return
        try:
            self.httpd = ReusableTCPServer(("", PORT), HTTPRequestHandler)
            self.is_running = True
            # print(f"Dashboard server started on http://localhost:{PORT}")
            self.httpd.serve_forever()
        except OSError as e:
            print(f"Failed to start server: {e}")
            self.is_running = False
        except Exception as e:
            print(f"Server error: {e}")
            self.is_running = False

    def start(self):
        if self.is_running:
            return
        try:
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
        except Exception as e:
            print(f"Failed to start dashboard server: {e}")

    def open_browser(self):
        if not self.is_running:
            print("Server is not running; cannot open browser.")
            return
        url = f"http://localhost:{PORT}/docs"
        # print(f"Opening browser at {url}")
        webbrowser.open(url)

    def stop(self):
        if self.httpd and self.is_running:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.is_running = False
            if self.server_thread:
                self.server_thread.join(timeout=1)
            # print("Dashboard server stopped")

# Global server instance
_dashboard_server = DashboardServer()

# Public API
def start_dashboard():
    _dashboard_server.start()

def open_dashboard():
    _dashboard_server.open_browser()

def stop_dashboard():
    _dashboard_server.stop()

def is_dashboard_running():
    return _dashboard_server.is_running

# Ensure shutdown on exit
atexit.register(stop_dashboard)
