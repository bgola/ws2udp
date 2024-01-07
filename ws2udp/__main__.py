#!/usr/bin/python

from ws2udp.ws2udp import run

import asyncio
import argparse
import logging

def main():
    parser = argparse.ArgumentParser(
        description="WebSocket to UDP proxy"
        )
    parser.add_argument("--udp-addr", default="localhost", help="Address of the UDP receiver for broadcasting messages (default=%(default)s)")
    parser.add_argument("--udp-port", default="57142", help="Port of the UDP receiver (default=%(default)s)")
    parser.add_argument("--fwd-fixed", action='store_true', help="Forward UDP to fixed target address/port")
    parser.add_argument("--fwd-addr", default="localhost", help="Address of the UDP target for messages (default=%(default)s)")
    parser.add_argument("--fwd-port", default="57143", help="Port of the UDP target (default=%(default)s)")
    parser.add_argument("--addr", default="0.0.0.0", help="WebSocket address to listen (default=%(default)s)")
    parser.add_argument("--port", default=8765, help="WebSocket port to listen (default=%(default)s)")
    parser.add_argument("--quiet", action='store_true', help="No verbose output")

    args = parser.parse_args()

    if args.quiet:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    udp_addr = (args.udp_addr, int(args.udp_port))
    logging.info(f"Forwarding WebSocket messages received on {args.addr}:{args.port}")
    logging.info(f"Broadcasting UDP messages received on {args.udp_addr}:{args.udp_port}")
    if args.fwd_fixed:
        fwd_addr = (args.fwd_addr, int(args.fwd_port))
        logging.info(f"Forwarding UDP messages to {args.fwd_addr}:{args.fwd_port}")
    else:
        fwd_addr = None

    try:
        asyncio.run(run(udp_addr, args.addr, args.port, fwd_addr=fwd_addr))
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logging.info("Quitting...")
