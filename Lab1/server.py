import socket
import sys
import os
import mimetypes
from pathlib import Path

class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
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
                self.handle_client(client_socket)
                client_socket.close()
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.socket.close()
    
    def handle_client(self, client_socket):
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
            
            if method != 'GET':
                self.send_response(client_socket, 404, "Not Found")  # Changed from 405 to 404
                return
            
            # Security: prevent directory traversal
            safe_path = Path(path.lstrip('/'))
            if '..' in safe_path.parts:
                self.send_response(client_socket, 404, "Not Found")  # Changed from 403 to 404
                return
            
            full_path = self.base_directory / safe_path
            
            if full_path.is_dir():
                self.serve_directory_listing(client_socket, full_path, path)
            elif full_path.is_file():
                self.serve_file(client_socket, full_path)
            else:
                self.send_response(client_socket, 404, "Not Found")
                
        except Exception as e:
            print(f"Error handling client: {e}")
            self.send_response(client_socket, 404, "Not Found")  # Changed from 500 to 404
    
    def serve_directory_listing(self, client_socket, directory_path, url_path):
        try:
            # Generate HTML directory listing
            items = []
            if url_path != '/':
                parent_path = str(Path(url_path).parent)
                if parent_path == '.':
                    parent_path = '/'
                items.append(f'<li><a href="{parent_path}">../</a></li>')
            
            for item in sorted(directory_path.iterdir()):
                if item.is_dir():
                    items.append(f'<li><a href="{os.path.join(url_path, item.name)}/">{item.name}/</a></li>')
                else:
                    items.append(f'<li><a href="{os.path.join(url_path, item.name)}">{item.name}</a></li>')
            
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
            self.send_response(client_socket, 404, "Not Found")  # Changed from 500 to 404
    
    def serve_file(self, client_socket, file_path):
        try:
            # Determine content type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # Check if file type is supported - now returns 404 instead of 415
            supported_types = ['text/html', 'image/png', 'application/pdf']
            if mime_type not in supported_types:
                self.send_response(client_socket, 404, "Not Found")  # Changed from 415 to 404
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
            self.send_response(client_socket, 404, "Not Found")  # Changed from 500 to 404
    
    def send_response(self, client_socket, status_code, status_message):
        # Simplified status map since we're only using 200 and 404 now
        status_map = {
            200: "OK",
            404: "Not Found"
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

def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        sys.exit(1)
    
    server = HTTPServer()
    server.serve_directory(directory)

if __name__ == "__main__":
    main()