#!/usr/bin/env python

from collections import deque

import asyncio
import logging
import socket
import struct
import websockets

udp_addr = None
clients = []

class UDPSock:
    """
    Class forked / modified from 
    https://github.com/bashkirtsevich-llc/aioudp
    """
    def __init__(self, addr='', port=0, loop=None, datagram_received=None):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setblocking(False)

        self._send_event = asyncio.Event()
        self._send_queue = deque()

        if loop is None:
            loop = asyncio.get_running_loop()

        if datagram_received is None:
            datagram_received = lambda msg, addr: None

        self._datagram_received_cb = datagram_received

        self.loop = loop
        self._sock.bind((addr, port))
       
        self._sender = asyncio.ensure_future(self._send_periodically())
        self._receiver = asyncio.ensure_future(self._recv_periodically())

    def sendto(self, data, addr):
        self._send_queue.append((data, addr))
        self._send_event.set()

    async def quit(self):
        self._sender.cancel()
        await self._sender
        self._receiver.cancel()
        await self._receiver
        self._sock.close()

    def getsockname(self):
        return self._sock.getsockname()

    def _run_future(self, *args):
        for fut in args:
            asyncio.ensure_future(fut, loop=self.loop)

    def _sock_recv(self, fut=None, registered=False):
        fd = self._sock.fileno()

        if fut is None:
            fut = self.loop.create_future()

        if registered:
            self.loop.remove_reader(fd)

        try:
            data, addr = self._sock.recvfrom(256 * 1024)
        except (BlockingIOError, InterruptedError):
            self.loop.add_reader(fd, self._sock_recv, fut, True)
        except Exception as e:
            fut.set_result(0)
        else:
            fut.set_result((data, addr))

        return fut

    def _sock_send(self, data, addr, fut=None, registered=False):
        fd = self._sock.fileno()

        if fut is None:
            fut = self.loop.create_future()

        if registered:
            self.loop.remove_writer(fd)

        if not data:
            return

        try:
            bytes_sent = self._sock.sendto(data, addr)
        except (BlockingIOError, InterruptedError):
            self.loop.add_writer(fd, self._sock_send, data, addr, fut, True)
        except Exception as e:
            fut.set_result(0)
        else:
            fut.set_result(bytes_sent)

        return fut

    async def _send_periodically(self):
        while True:
            await self._send_event.wait()
            try:
                while self._send_queue:
                    data, addr = self._send_queue.popleft()
                    bytes_sent = await self._sock_send(data, addr)
            finally:
                self._send_event.clear()

    async def _recv_periodically(self):
        while True:
            data, addr = await self._sock_recv()
            self._datagram_received(data, addr)

    def _datagram_received(self, data, addr):
        self._datagram_received_cb(data, addr)


class Client:
    """
    Simple representation of a websocket client.
    Keeps a map of ports used for proxying UDP messages and uses a queue
    for sending UDP messages back to the websocket.
    """
    def __init__(self, websocket):
        logging.info(f"New WebSocket client from {websocket.remote_address}")
        self.websocket = websocket
        
        self._sock = UDPSock(datagram_received=self._got_udp_message)
        logging.info(f"{self} listening to UDP messages on {self._sock.getsockname()}")

        self.queue = asyncio.Queue()

    def __repr__(self):
        return f"Client{self.websocket.remote_address}"

    def send_udp(self, message, addr):
        logging.info(f"Sending to UDP: {self.websocket.remote_address} ~> {message} ~> {addr}")
        self._sock.sendto(message, addr)

    def send_ws(self, message):
        logging.info(f"Sending to WebSocket: {self._sock.getsockname()} ~> {message} ~> {self.websocket.remote_address}")
        try:
            self.queue.put_nowait(message)
        except asyncio.QueueFull:
            logging.warning(f"Can't send mesage to {self}, queue is full")

    async def leave(self):
        await self._sock.quit()

    def _start_listening(self):
        loop = asyncio.get_running_loop()
        self._sock.bind(('', 0))
        asyncio.ensure_future(self._recv(), loop=asyncio.get_running_loop())

    def _got_udp_message(self, message, addr):
        self.send_ws(message)


async def ws2udp_sender(client):
    """
    Sends UDP message received to WebSocket
    """
    while True:
        message = await client.queue.get()
        await client.websocket.send(message)


async def ws2udp_receiver(client):
    """
    Receives UDP message via WebSocket and forwards to UDP.
    """
    async for message in client.websocket:
        # Parse addres and port where to send
        # Format is [addr_string_length:uint32][addr:string][port:uint32][message]
        original_message = message[:]
        try:
            addr_size = struct.unpack("I", message[:4])[0]
            message = message[4:]
            addr = message[:addr_size]
            message = message[addr_size:]
            port = struct.unpack("I", message[:4])[0]
            message = message[4:]
        except TypeError:
            logging.error(f"Got a bad message, can't parse address to forward: {original_message}")
        else:
            client.send_udp(message, (addr, port))


async def ws2udp_handler(websocket, path):
    """
    Wrapper handler for both way communication.
    """
    client = Client(websocket)
    clients.append(client)

    receiver = asyncio.ensure_future(
        ws2udp_receiver(client))
    sender = asyncio.ensure_future(
        ws2udp_sender(client))
    
    try:
        done, pending = await asyncio.wait(
            [receiver, sender],
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        for task in pending:
            task.cancel()
        for task in done:
            # trigger exceptions, if any
            task.result()
    except (
            websockets.exceptions.ConnectionClosedError,
            websockets.exceptions.ConnectionClosedOK,
            asyncio.exceptions.CancelledError):
        # Connection ended
        pass

    logging.info(f"Client {client.websocket.remote_address} left")
    await client.leave()
    clients.remove(client)


async def run(udp_addr, websocket_addr, websocket_port):
    ws_server = await websockets.serve(ws2udp_handler, websocket_addr, websocket_port)

    def send_broadcast(message, addr):
        for client in clients:
            client.send_ws(message)

    udp_server = UDPSock(*udp_addr, datagram_received=send_broadcast)  
    await ws_server.server.serve_forever()
