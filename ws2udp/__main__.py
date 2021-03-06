#!/usr/bin/python

from ws2udp.ws2udp import run

import asyncio
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(
        description="WebSocket to UDP proxy"
        )
    parser.add_argument("--udp-addr", default="localhost", help="Address of the UDP receiver for broadcasting messages (default=localhost)")
    parser.add_argument("--udp-port", default="57142", help="Port of the UDP receiver (default=57142)")
    parser.add_argument("--addr", default="0.0.0.0", help="WebSocket address to listen (default=0.0.0.0)")
    parser.add_argument("--port", default=8765, help="WebSocket port to listen (default=8765)")
    parser.add_argument("--quiet", action='store_true', help="No verbose output")
    
    args = parser.parse_args()

    if args.quiet:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    udp_addr = (args.udp_addr, int(args.udp_port))
    logging.info(f"Forwarding WebSocket messages received on {args.addr}:{args.port}")
    logging.info(f"Broadcasting UDP messages received on {args.udp_addr}:{args.udp_port}")

    try:
        asyncio.run(run(udp_addr, args.addr, args.port))
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logging.info("Quitting...")
