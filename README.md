# Panoramic Power Bridge Data Collection

## Project Goal

The objective of this project is to intercept and analyze data sent by the Centrica Business Solutions PowerRadar® and Panoramic Power cellular bridge hardware, which traditionally communicates with a remote cloud server. The goal is to understand its protocol, extract useful data, and explore possible local data collection and processing options.

## Current Progress

At this stage, the exact communication protocol and data format are unknown. This document serves as a record of progress in capturing and analyzing the bridge's outgoing data. Contributions and insights from others with expertise in protocol analysis, embedded systems, or network forensics are welcome.

## Device Specifications

- **Model**: Panoramic Power Advanced Cellular Bridge (Gen1/Gen2)
- **Firmware**: v2x (Build 107)
- **Default Endpoint**: `col.panpwrws.com:8051` (unencrypted TCP)
- **Sensor Protocol**: Proprietary wireless on ISM 915MHz (US) or 434MHz (EU)
- **Sensor Transmission Rate**: \~10 seconds per update
- **Bridge Range**: \~5m (16ft) from sensors
- **Security**: No TLS support

## Capturing Data from the Bridge

### Required Tools

For Arch Linux:

```bash
sudo pacman -S tcpdump wireshark-qt tshark netcat socat
```

### Bridge Configuration Steps

1. Enter configuration mode:
   - Hold the **config button** for \~5 seconds until LED turns solid red.
2. Connect directly via Ethernet.
3. Access the web interface at `http://10.0.0.10`.
4. Login with: `panpwr/panpwr`.
5. Navigate to **Administration**.
6. Change "Main Panoramic server host" to your local server IP.
7. Keep the port as `8051`.
8. Save settings and reboot the bridge.

### Capturing TCP Traffic

#### Basic TCP Listener

```bash
# Capture raw traffic
sudo tcpdump -i eth0 port 8051 -w capture.pcap

# Simple netcat listener
nc -l 8051 | tee raw_data.bin | hexdump -C

# Persistent logging using socat
socat TCP-LISTEN:8051,fork,reuseaddr OPEN:bridge_data.log,creat,append
```

#### Python TCP Server (`bridge_server.py` / `bridge_server_response.py`)

This script sets up a TCP server on port `8051` to capture raw data sent by the bridge. It:

- Listens for incoming connections and maintains persistence
- Logs raw binary data and hex-formatted logs with timestamps
- Provides real-time console output with logging
- Handles connection errors and reconnections

The `bridge_server_response.py` script adds a response as captured from [Bridge Proxy](#bridge-proxy-bridge_proxypy) ([bridge_proxy.log](#bridge_proxylog))

#### Bridge Proxy (`bridge_proxy.py`)

This script acts as a transparent proxy, capturing bidirectional traffic between the bridge and the original remote server (`col.panpwrws.com`). It:

- Intercepts and logs the data sent by the bridge
- Relays the data to `col.panpwrws.com`
- Captures and logs responses from the remote server

### Analyzing Captured Data

#### Log Files Generated:

- `bridge_data.log`: Raw binary data received from the bridge in its original format
- `bridge_data_hex.log`: Human-readable hexadecimal representation with timestamps
- `bridge_server.log`: Server activities (connections, errors, etc.)
- `bridge_proxy.log` - Captured bidirectional traffic between the bridge and `col.panpwrws.com`, including both sent and received messages

#### Log File Analysis:

```bash
# View raw data in hex format
xxd bridge_data.log > bridge_data_hex_view.txt
hexdump -C bridge_data.log

tail -f bridge_server.log  # Monitor server activity
```

#### Converting Logs to PCAP for Wireshark Analysis

```bash
text2pcap -T 8051,8051 bridge_data.log bridge_data.pcap
wireshark bridge_data.pcap
```

Filters in Wireshark:

- `tcp.port == 8051`
- "Follow TCP Stream"

## Technical Findings (Ongoing Investigation)

### 2025-03-22 Micron N25Q256A
Board component: U45, 8-Lead, VDFPN8 – MLP8 
Flash Memory BIN dumped.
Size: 33 554 432 bytes (33,6 MB)

### Initial Observations from Captured Data

#### `bridge_data_hex.log`

The log contains structured binary messages with repeating patterns, likely containing sensor IDs, power readings, and possible control messages. Examples:

```
1742548731 - 192.168.2.246:2655 - 5555840010280e0001170006003300000000000d0010280e00061f00b90500000031b901...
1742548731 - 192.168.2.246:2655 - 55550b0010280e00000102416b004c3f
1742548731 - 192.168.2.246:2655 - 55550b001eef0f0051020d7c01001c52
```

- The `5555` prefix appears consistent, possibly an indicator for message headers.
- Variable-length data fields suggest different message types.
- Some sections seem to contain structured counters or identifiers.

#### `bridge_proxy.log`

Captured interactions between the bridge and `col.panpwrws.com`:

```
2025-03-21 11:41:32,100 - INFO: CLIENT_TO_SERVER -> 55550b0010280e00000102416b004c3f
2025-03-21 11:41:32,212 - INFO: SERVER_TO_CLIENT -> 5a
2025-03-21 11:41:32,219 - INFO: CLIENT_TO_SERVER -> 55550d0010280e000112000402416b004c97
2025-03-21 11:41:32,330 - INFO: SERVER_TO_CLIENT -> 5a
```

- The bridge sends structured messages to the cloud server.
- The cloud server responds with simple `5a` acknowledgments, suggesting minimal interaction beyond message reception.
- Some messages contain data payloads that might correspond to sensor values or configuration updates.

### Next Steps

- Further reverse engineering to map data fields to meaningful metrics.
- Identifying message types (sensor data, keep-alives, configuration updates).
- Investigating why `bridge_data.log` does not convert to PCAP.
- Exploring how responses from `col.panpwrws.com` influence the bridge's behavior.
- Setup the sensors over [controlled load](#controlled-power-supply-test)

### Controlled power supply test

This will allow to collect data that can be referenced and would help identify:

- Sensor Data Mapping
  - Use variable load (e.g., 2A vs 4A) on same sensor
  - Compare hexdump to find changing byte sequences
  - Correlate changes to specific data fields
- Multi-Sensor Scenario
  - Add sensors with known, controlled current draws
  - Observe protocol's handling of multiple sensor data streams
- Identify:
  - Sensor ID encoding
  - Data sequence/interleaving
  - Potential checksums or metadata

Recommended Equipment:
 - Adjustable DC power supply
 - Current shunt resistors
 - Precision current measurement tools

Experimental Protocol:
 - Log hex data during controlled current changes
 - Use systematic, documented current step variations
 - Capture extended communication sequences

### Bridge Storage Limits (Estimates)

| Connected Sensors | Storage Duration |
| ----------------- | ---------------- |
| 10                | \~10 days        |
| 20                | \~5 days         |
| 100               | \~1 day          |
| 200               | \~0.5 days       |

### Bridge LED Indicators

- **Power LED (Green)**: Device is powered
- **Middle LED (Blinking Orange)**: Receiving sensor data
- **Middle LED (Solid Red)**: Configuration mode
- **Link LED (Off)**: No network
- **Link LED (Blinking Green)**: Connected to network, not the server
- **Link LED (Solid Green)**: Connected to the server

### Other Features

- Older firmware (v2x) **does not support Modbus TCP**.
- Newer firmware (v471+) supports **Modbus TCP (port 502)**.
- Telnet access available on port 20 (in configuration mode).
- All communications are **outbound-only**.

---

This is an ongoing project where the ultimate goal is still being determined. The information provided outlines the progress made so far and the methods used to collect data. Contributions are welcome, especially in protocol analysis and data interpretation.

