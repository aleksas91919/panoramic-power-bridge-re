I have a Panoramic Power/Centrica bridge device (Gen1/Gen2 with firmware version 2x, Build 107) and need to set up a local server to capture data from this device instead of sending it to the Centrica cloud servers. 

## My Device Specifications
- Model: Panoramic Power Advanced Cellular Bridge
- Hardware Generation: Gen1/Gen2
- Firmware Version: Version 2x (Build 107)
- Default cloud connection: col.panpwrws.com:8051

## Communication Details
- This older firmware version communicates with the cloud via TCP on port 8051 (not TLS)
- The bridge collects readings from wireless sensors that transmit on proprietary protocol over ISM 915MHz (US) or 434MHz (EU) band
- Sensors transmit readings approximately every 10 seconds
- Bridge configuration is done via web interface at 10.0.0.10 when the bridge is in configuration mode
- Default administrator credentials: username/password are both "panpwr"

## Local Server Requirements
To capture data locally, I need to set up:
1. A TCP server listening on port 8051
2. Configure the bridge to point to my local server IP address instead of col.panpwrws.com
3. Implement a custom protocol handler to parse and store the incoming data

## Bridge Configuration Steps
1. I'll need to configure the bridge to communicate with my local server by:
   - Placing the bridge in configuration mode (pressing Config button for ~5 seconds until LED is solid red)
   - Connecting directly via Ethernet and accessing the web interface at 10.0.0.10
   - Navigating to Administration settings
   - Changing "Main Panoramic server host" from col.panpwrws.com to my local server IP
   - Keeping the port as 8051

## Modbus TCP Information
The newer firmware (v471+) documentation indicates that the bridge can be set to "Stand-Alone Modbus TCP" mode, but it's unclear if my older firmware supports this. If available, this would allow:
- Bridge acting as a Modbus TCP slave on port 502
- A Modbus master could poll the bridge for sensor data
- Calibrated sensor readings would be available via register reads

## Implementation Challenges
- The exact protocol format over TCP port 8051 is not documented
- I'll need to analyze traffic between the bridge and cloud to reverse engineer it
- Time synchronization may be an issue since the bridge uses NTP

Please help me determine if it's feasible to intercept this data with my older firmware version, and what approach would work best for my specific device configuration.
