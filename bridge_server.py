#!/usr/bin/env python3
import socket
import binascii
import logging
import time
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bridge_server.log"),
        logging.StreamHandler()
    ]
)

# Configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8051       # Panoramic Power bridge port
DATA_LOG = 'bridge_data.log'
HEX_LOG = 'bridge_data_hex.log'

def ensure_dir_exists(file_path):
    """Make sure the directory for the file exists"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def log_data(data, client_addr):
    """Log the received binary data to files"""
    timestamp = int(time.time())
    hex_data = binascii.hexlify(data).decode('utf-8')

    # Log binary data
    with open(DATA_LOG, 'ab') as f:
        f.write(data)

    # Log hex data with timestamp and source
    with open(HEX_LOG, 'a') as f:
        f.write(f"{timestamp} - {client_addr[0]}:{client_addr[1]} - {hex_data}\n")

def main():
    # Create server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
        server.listen(5)
        logging.info(f"Panoramic Power bridge server listening on {HOST}:{PORT}")

        # Ensure log files exist
        ensure_dir_exists(DATA_LOG)
        ensure_dir_exists(HEX_LOG)

        while True:
            client, addr = server.accept()
            logging.info(f"Connection established from {addr[0]}:{addr[1]}")

            try:
                # Handle this client connection
                while True:
                    data = client.recv(4096)
                    if not data:
                        logging.info(f"Connection closed by {addr[0]}:{addr[1]}")
                        break

                    # Log the received data
                    log_data(data, addr)

                    # Display info about the received data
                    hex_data = binascii.hexlify(data).decode('utf-8')
                    logging.info(f"Received {len(data)} bytes from {addr[0]}:{addr[1]}")
                    logging.info(f"First 60 bytes (hex): {hex_data[:120]}...")

                    # TODO: Implement proper response once protocol is understood
                    # For now just send a dummy acknowledgment
                    # client.send(b'\x00\x00')

            except Exception as e:
                logging.error(f"Error handling client {addr[0]}:{addr[1]}: {e}")

            finally:
                client.close()

    except KeyboardInterrupt:
        logging.info("Server shutting down (Ctrl+C)")

    except Exception as e:
        logging.error(f"Server error: {e}")

    finally:
        server.close()
        logging.info("Server stopped")

if __name__ == "__main__":
    main()
