import os
import logging
import json
import socket

# For testing start up a python server using:
# python -m http.server 8000 --bind 127.0.0.1

def is_port_open(ip: str, port: int, timeout: float = 2.0) -> bool:
    logging.info(f"Testing {ip} on port {port}")
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def run_tcp_connectivity(target_ip, ports):
    results = []

    # Perform TCP connectivity tests.
    for port in ports:
        if is_port_open(target_ip, port):
            print(f"Port {port} on {target_ip} is OPEN")
            results.append({"port": port, "status": "OPEN"})
        else:
            print(f"Port {port} on {target_ip} is CLOSED or filtered")
            results.append({"port": port, "status": "CLOSED or filtered"})

    logging.info(f"TCP connectivity results for {target_ip}: {results}")
    return results