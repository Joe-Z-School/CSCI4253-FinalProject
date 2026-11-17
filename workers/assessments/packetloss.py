import logging
from icmplib import ping


def run_packetloss(target_ip):
    logging.info(f"Running packet loss test for {target_ip}")

    host = ping(
        target_ip,
        count=20,
        interval=0.2,
        privileged=False
    )

    logging.info(f"Packet loss: {host.packet_loss:.1f}%")

    results = [
        {
            'metric_name': 'packets_sent',
            'metric_value': host.packets_sent,
            'unit': 'packets',
            'port': None
        },
        {
            'metric_name': 'packets_received',
            'metric_value': host.packets_received,
            'unit': 'packets',
            'port': None
        },
        {
            'metric_name': 'packets_lost',
            'metric_value': host.packets_sent - host.packets_received,
            'unit': 'packets',
            'port': None
        },
        {
            'metric_name': 'packet_loss',
            'metric_value': host.packet_loss,
            'unit': '%',
            'port': None
        }
    ]

    return results