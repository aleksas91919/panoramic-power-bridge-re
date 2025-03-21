#!/usr/bin/env python3
import socket
import logging
import binascii
import threading
import time
import errno
import pcapy
from scapy.all import wrpcap, IP, TCP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='bridge_proxy.log',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

class BridgePcapProxy:
    def __init__(self, local_port=8051, pcap_filename='bridge_capture.pcap'):
        self.local_port = local_port
        self.pcap_filename = pcap_filename
        self.running = True
        self.server_socket = None
        self.pcap_packets = []

    def forward_traffic(self, source, destination, direction, client_addr):
        try:
            while self.running:
                try:
                    source.settimeout(1)
                    data = source.recv(4096)
                    if not data:
                        break

                    # Log hex data
                    hex_data = binascii.hexlify(data).decode('utf-8')
                    logging.info(f"{direction} -> {hex_data}")

                    # Construct Scapy packet for PCAP
                    if client_addr:
                        ip_packet = IP(src=client_addr[0], dst='col.panpwrws.com')
                        tcp_packet = TCP(sport=client_addr[1], dport=8051)
                        scapy_packet = ip_packet/tcp_packet/data
                        self.pcap_packets.append(scapy_packet)

                    # Simple ACK response to keep bridge connected
                    destination.send(b'\x5a')

                except socket.timeout:
                    continue
                except (OSError, IOError) as e:
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

    def handle_client(self, client_socket, client_addr):
        try:
            logging.info(f"Handling connection from {client_addr}")

            # Forward traffic in both directions
            client_to_proxy = threading.Thread(
                target=self.forward_traffic,
                args=(client_socket, client_socket, 'CLIENT_TO_SERVER', client_addr)
            )
            client_to_proxy.start()

            client_to_proxy.join()

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

                    client_handler = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr)
                    )
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

        # Write captured packets to PCAP
        if self.pcap_packets:
            wrpcap(self.pcap_filename, self.pcap_packets)
            logging.info(f"Saved {len(self.pcap_packets)} packets to {self.pcap_filename}")

        logging.info("Proxy server stopped")

def main():
    proxy = BridgePcapProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\nStopping proxy...")
        proxy.stop()

if __name__ == '__main__':
    main()
