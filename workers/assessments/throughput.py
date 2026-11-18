"""
This function measures TCP throughput by starting a iperf3 client that connects
to a iperf3 server running on the target machine. It captures the output of the
iperf3 command and parses the JSON output to extract the throughput information.
The throughput is measured in bits per second and converted to megabits per second.
The function returns a dictionary containing the test type, status, target IP,
port, duration, protocol, and the measured throughput in both bits per second and
megabits per second. 

In case of errors, it returns a dictionary with the test type, status, target IP, 
and an error message. The function uses the subprocess module to run the iperf3 
command and handles exceptions for timeouts, command errors, and JSON parsing errors.
"""

import json
import logging
import subprocess


def run_throughput(target_ip, port=5201, duration=10):
    command = [
        "iperf3",
        "-c", str(target_ip),
        "-p", str(port),
        "-t", str(duration),
        "-J"
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=duration + 15,
            check=True
        )

        data = json.loads(result.stdout)

        # Prefer the receiver's measured throughput.
        throughput = data["end"]["sum_received"]["bits_per_second"]

        # Convert bits per second to megabits per second.
        throughput_mbps = throughput / 1000000

        results = [
            {
                'ip': target_ip, 
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput', 
                'metric_value': round(throughput_mbps, 2), 
                'unit': 'Mbps',
                'status': 'completed'
            },
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput_bps',
                'metric_value': throughput,
                'unit': 'bps',
                'status': 'completed'
            }
        ]

        return results

    except subprocess.TimeoutExpired:
        logging.error("Throughput test timed out for %s", target_ip)

        results = [
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput',
                'metric_value': None,
                'unit': 'Mbps',
                'status': 'failed',
                'error': 'Throughput test timed out'
            },
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput_bps',
                'metric_value': None,
                'unit': 'bps',
                'status': 'failed',
                'error': 'Throughput test timed out'
            }
        ]

        return results

    except subprocess.CalledProcessError as error:
        logging.error("Throughput test failed for %s: %s",target_ip,error.stderr)

        results = [
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput',
                'metric_value': None,
                'unit': 'Mbps',
                'status': 'failed',
                'error': error.stderr.strip()
            },
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput_bps',
                'metric_value': None,
                'unit': 'bps',
                'status': 'failed',
                'error': error.stderr.strip()
            }
        ]

        return results

    except (json.JSONDecodeError, KeyError, TypeError) as error:
        logging.error("Unable to parse throughput results: %s", error)

        results = [
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput',
                'metric_value': None,
                'unit': 'Mbps',
                'status': 'failed',
                'error': 'Unable to parse iperf3 results'
            },
            {
                'ip': target_ip,
                'duration': duration,
                'protocol': 'TCP',
                'metric_name': 'throughput_bps',
                'metric_value': None,
                'unit': 'bps',
                'status': 'failed',
                'error': 'Unable to parse iperf3 results'
            }
        ]

        return results