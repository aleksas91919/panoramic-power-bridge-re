#!/usr/bin/env python3
import socket
import logging
import binascii
import threading
import time
import errno

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='bridge_proxy.log',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

class BridgeProxy:
    def __init__(self, local_port=8051, remote_host='col.panpwrws.com', remote_port=8051):
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.running = True
        self.server_socket = None

    def forward_traffic(self, source, destination, direction):
        try:
            while self.running:
                try:
                    source.settimeout(1)
                    data = source.recv(4096)
                    if not data:
                        break
                    
                    hex_data = binascii.hexlify(data).decode('utf-8')
                    logging.info(f"{direction} -> {hex_data}")
                    
                    destination.send(data)
                except socket.timeout:
                    continue
                except (OSError, IOError) as e:
                    # Ignore specific socket errors that can occur during shutdown
                    if e.errno in [errno.EBADF, errno.ECONNRESET, errno.EPIPE]:
                        break
                    raise
        except Exception as e:
            logging.error(f"Error in {direction} forwarding: {e}")
        finally:
            try:
                source.close()
            except:
                pass
            try:
                destination.close()
            except:
                pass

    def handle_client(self, client_socket):
        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((self.remote_host, self.remote_port))
            
            logging.info(f"Connected to {self.remote_host}:{self.remote_port}")

            client_to_remote = threading.Thread(target=self.forward_traffic, 
                                      args=(client_socket, remote_socket, 'CLIENT_TO_SERVER'))
            remote_to_client = threading.Thread(target=self.forward_traffic, 
                                      args=(remote_socket, client_socket, 'SERVER_TO_CLIENT'))
            
            client_to_remote.start()
            remote_to_client.start()
            
            client_to_remote.join()
            remote_to_client.join()

        except Exception as e:
            logging.error(f"Error handling client connection: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.local_port))
            self.server_socket.listen(5)
            
            logging.info(f"Proxy listening on port {self.local_port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    logging.info(f"Accepted connection from {addr}")
                    
                    client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                    client_handler.start()
                except socket.timeout:
                    continue

        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logging.info("Proxy server stopped")

def main():
    proxy = BridgeProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\nStopping proxy...")
        proxy.stop()

if __name__ == '__main__':
    main()
