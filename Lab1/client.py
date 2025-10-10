import socket
import sys
import os
import urllib.parse
from pathlib import Path

class HTTPClient:
    def __init__(self):
        self.supported_binary_types = ['image/png', 'application/pdf']
    
    def download(self, server_host, server_port, url_path, save_directory):
        try:
            # Create save directory if it doesn't exist
            save_path = Path(save_directory)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Connect to server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((server_host, server_port))
                
                # Send HTTP request
                request = f"GET {url_path} HTTP/1.1\r\n"
                request += f"Host: {server_host}:{server_port}\r\n"
                request += "Connection: close\r\n\r\n"
                
                sock.send(request.encode('utf-8'))
                
                # Receive response
                response = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                
                # Parse response
                header_end = response.find(b"\r\n\r\n")
                if header_end == -1:
                    print("Invalid response from server")
                    return
                
                headers = response[:header_end].decode('utf-8')
                body = response[header_end + 4:]
                
                # Parse status line
                status_line = headers.split('\r\n')[0]
                status_parts = status_line.split()
                if len(status_parts) < 2:
                    print("Invalid status line")
                    return
                
                status_code = int(status_parts[1])
                
                if status_code != 200:
                    print(f"Server returned status: {status_code}")
                    if body:
                        print(body.decode('utf-8', errors='ignore'))
                    return
                
                # Parse headers
                content_type = None
                for line in headers.split('\r\n')[1:]:
                    if line.lower().startswith('content-type:'):
                        content_type = line.split(':', 1)[1].strip()
                        break
                
                # Handle based on content type
                if content_type and any(ct in content_type for ct in self.supported_binary_types):
                    # Extract filename from URL
                    filename = os.path.basename(url_path)
                    if not filename or filename == '/':
                        filename = 'downloaded_file'
                    
                    # Add appropriate extension if missing
                    if content_type == 'image/png' and not filename.lower().endswith('.png'):
                        filename += '.png'
                    elif content_type == 'application/pdf' and not filename.lower().endswith('.pdf'):
                        filename += '.pdf'
                    
                    file_path = save_path / filename
                    
                    # Save binary file
                    with open(file_path, 'wb') as f:
                        f.write(body)
                    
                    print(f"File saved: {file_path}")
                    print(f"Size: {len(body)} bytes")
                    
                else:
                    # Assume HTML or text, print to console
                    try:
                        text_content = body.decode('utf-8')
                        print(text_content)
                    except UnicodeDecodeError:
                        print("Received binary content of unsupported type")
                        print(f"Content-Type: {content_type}")
                        print(f"Size: {len(body)} bytes")
                        
        except socket.timeout:
            print("Connection timeout")
        except ConnectionRefusedError:
            print(f"Could not connect to {server_host}:{server_port}")
        except Exception as e:
            print(f"Error: {e}")

def main():
    if len(sys.argv) != 5:
        print("Usage: python client.py server_host server_port url_path directory")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    url_path = sys.argv[3]
    save_directory = sys.argv[4]
    
    client = HTTPClient()
    client.download(server_host, server_port, url_path, save_directory)

if __name__ == "__main__":
    main()