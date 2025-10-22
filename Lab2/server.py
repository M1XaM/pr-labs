import socket
import sys
import os
import mimetypes
from pathlib import Path
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # For request counting - thread-safe implementation
        self.request_counters = {}
        self.counter_lock = threading.Lock()
        
        # For rate limiting
        self.client_requests = {}
        self.rate_limit_lock = threading.Lock()
        self.rate_limit = 10
        
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
    
    def serve_directory(self, base_directory):
        self.base_directory = Path(base_directory).resolve()
        print(f"Serving directory: {self.base_directory}")
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Server running on http://{self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")
                
                self.thread_pool.submit(self.handle_client_thread, client_socket, client_address)
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
            self.thread_pool.shutdown(wait=False)
        finally:
            self.socket.close()
    
    def handle_client_thread(self, client_socket, client_address):
        try:
            self.handle_client(client_socket, client_address)
        finally:
            client_socket.close()
    
    def check_rate_limit(self, client_ip):
        with self.rate_limit_lock:
            now = time.time()
            
            # Initialize or clean up old requests for this IP
            if client_ip not in self.client_requests:
                self.client_requests[client_ip] = []
            
            # Remove requests older than 1 second
            self.client_requests[client_ip] = [
                timestamp for timestamp in self.client_requests[client_ip]
                if now - timestamp < 1.0
            ]
            
            # Check if under limit
            if len(self.client_requests[client_ip]) < self.rate_limit:
                self.client_requests[client_ip].append(now)
                return True
            else:
                return False
    
    def handle_client(self, client_socket, client_address):
        try:
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data:
                return
            
            lines = request_data.split('\r\n')
            if not lines:
                return
            
            request_line = lines[0]
            parts = request_line.split()
            if len(parts) < 2:
                return
            
            method, path = parts[0], parts[1]
            
            # Rate limiting check
            client_ip = client_address[0]
            if not self.check_rate_limit(client_ip):
                self.send_response(client_socket, 429, "Too Many Requests")
                print(f"Rate limit exceeded for {client_ip}")
                return
            
            if method != 'GET':
                self.send_response(client_socket, 404, "Not Found")
                return
            
            # Security: prevent directory traversal
            safe_path = Path(path.lstrip('/'))
            if '..' in safe_path.parts:
                self.send_response(client_socket, 404, "Not Found")
                return
            
            full_path = self.base_directory / safe_path
            
            # Simulate work 1 second delay
            time.sleep(1)
            # time.sleep(0.01)
            
            # ----- RACE CONDITION SIMULATION ------
            self.update_request_counter(str(full_path))
            # self.race_condition_counter(str(full_path))
            
            if full_path.is_dir():
                self.serve_directory_listing(client_socket, full_path, path)
            elif full_path.is_file():
                self.serve_file(client_socket, full_path)
            else:
                self.send_response(client_socket, 404, "Not Found")
                
        except Exception as e:
            print(f"Error handling client: {e}")
            self.send_response(client_socket, 404, "Not Found")
    
    def update_request_counter(self, file_path):
        with self.counter_lock:
            if file_path in self.request_counters:
                self.request_counters[file_path] += 1
            else:
                self.request_counters[file_path] = 1
            print(f"Updated {file_path} to {self.request_counters[file_path]}")

    
    def race_condition_counter(self, file_path):
        if file_path in self.request_counters:
            import time
            time.sleep(0.1)
            self.request_counters[file_path] += 1
        else:
            self.request_counters[file_path] = 1
        print(f"Updated {file_path} to {self.request_counters[file_path]}")

    
    def get_request_count(self, file_path):
        with self.counter_lock:
            return self.request_counters.get(file_path, 0)
    
    def serve_directory_listing(self, client_socket, directory_path, url_path):
        try:
            # Generate HTML directory listing with request counts
            items = []
            if url_path != '/':
                parent_path = str(Path(url_path).parent)
                if parent_path == '.':
                    parent_path = '/'
                parent_full_path = str(self.base_directory / parent_path.lstrip('/'))
                parent_count = self.get_request_count(parent_full_path)
                items.append(f'<li><a href="{parent_path}">../</a> (Requests: {parent_count})</li>')
            
            for item in sorted(directory_path.iterdir()):
                item_full_path = str(item)
                count = self.get_request_count(item_full_path)
                if item.is_dir():
                    items.append(f'<li><a href="{os.path.join(url_path, item.name)}/">{item.name}/</a> (Requests: {count})</li>')
                else:
                    items.append(f'<li><a href="{os.path.join(url_path, item.name)}">{item.name}</a> (Requests: {count})</li>')
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Directory listing for {url_path}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ margin: 5px 0; }}
                    a {{ text-decoration: none; color: #0366d6; }}
                    a:hover {{ text-decoration: underline; }}
                    .count {{ color: #666; font-size: 0.9em; margin-left: 10px; }}
                </style>
            </head>
            <body>
                <h1>Directory listing for {url_path}</h1>
                <ul>
                {''.join(items)}
                </ul>
            </body>
            </html>
            """
            
            response = f"HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/html; charset=utf-8\r\n"
            response += f"Content-Length: {len(html_content.encode('utf-8'))}\r\n"
            response += "Connection: close\r\n\r\n"
            response += html_content
            
            client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Error generating directory listing: {e}")
            self.send_response(client_socket, 404, "Not Found")
    
    def serve_file(self, client_socket, file_path):
        try:
            # Determine content type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # Check if file type is supported
            supported_types = ['text/html', 'text/plain', 'image/png', 'application/pdf']
            if mime_type not in supported_types:
                self.send_response(client_socket, 404, "Not Found")
                return
            
            with open(file_path, 'rb') as file:
                content = file.read()
            
            response = f"HTTP/1.1 200 OK\r\n"
            response += f"Content-Type: {mime_type}\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += "Connection: close\r\n\r\n"
            
            client_socket.send(response.encode('utf-8'))
            client_socket.send(content)
            
        except FileNotFoundError:
            self.send_response(client_socket, 404, "Not Found")
        except Exception as e:
            print(f"Error serving file: {e}")
            self.send_response(client_socket, 404, "Not Found")
    
    def send_response(self, client_socket, status_code, status_message):
        status_map = {
            200: "OK",
            404: "Not Found",
            429: "Too Many Requests"
        }
        
        message = status_map.get(status_code, status_message)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{status_code} {message}</title>
        </head>
        <body>
            <h1>{status_code} {message}</h1>
        </body>
        </html>
        """
        
        response = f"HTTP/1.1 {status_code} {message}\r\n"
        response += "Content-Type: text/html; charset=utf-8\r\n"
        response += f"Content-Length: {len(html_content.encode('utf-8'))}\r\n"
        response += "Connection: close\r\n\r\n"
        response += html_content
        
        client_socket.send(response.encode('utf-8'))

class SingleThreadedHTTPServer(HTTPServer):
    def serve_directory(self, base_directory):
        self.base_directory = Path(base_directory).resolve()
        print(f"Serving directory: {self.base_directory}")
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            print(f"Single-threaded server running on http://{self.host}:{self.port}")
            
            while True:
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")
                self.handle_client(client_socket, client_address)
                client_socket.close()
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.socket.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    # Default server type
    default_server_type = "1"  # 1 = multithreaded, 2 = single-threaded

    # Use environment variable to decide default vs interactive
    use_defaults = os.environ.get("USE_DEFAULTS", "0").lower() in ("1", "true", "yes")

    if use_defaults:
        choice = default_server_type
        print(f"USE_DEFAULTS is set → starting multithreaded server automatically with directory '{directory}'")
    else:
        # Interactive mode
        print("Choose server type:")
        print("1. Multithreaded (default)")
        print("2. Single-threaded")
        choice = input("Enter choice (1 or 2): ").strip() or default_server_type

    if choice == "2":
        server = SingleThreadedHTTPServer()
        print("Starting single-threaded server...")
    else:
        server = HTTPServer()
        print("Starting multithreaded server...")

    server.serve_directory(directory)

if __name__ == "__main__":
    main()