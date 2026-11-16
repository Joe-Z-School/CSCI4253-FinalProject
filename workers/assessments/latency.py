import os
import logging
import json
import socket
import time

# For testing start up a python server using:
# python -m http.server 8000 --bind 127.0.0.1

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_tcp_latency(ip: str, port: int = 8000, timeout: float = 3.0) -> float | None:
    start_time = time.perf_counter()
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            end_time = time.perf_counter()
            logging.info(f"Successfully connected to {ip}:{port}. Latency: {round((end_time - start_time) * 1000, 2)} ms")
            return round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
    except (socket.timeout, ConnectionRefusedError, OSError):
        logging.warning(f"Failed to test TCP latency to {ip}:{port}")
        return None


def run_latency(target_ip):
    results = []

    latency = test_tcp_latency(target_ip)
    results.append({"ip": target_ip, 'metric_name': "latency", "metric_value": latency, "unit": "ms"})
    return results