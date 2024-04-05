# ws2udp

A WebSocket to UDP proxy. 

**ws2udp** will forward messages coming from the WebSocket server to UDP sockets, it is especially useful
to send OSC messages from JavaScript applications to SuperCollider or any other software that doesn't support
WebSockets. It registers all websockets connected and will broadcast messages sent to its own UDP port.

## Installation

You will need Python>=3.7 and the websockets package.

The simplest way to install is using pip:

`$ pip install ws2udp`

## Example

```
$ ws2udp
WebSocket to UDP proxy

optional arguments:
  -h, --help           show this help message and exit
  --udp-addr UDP_ADDR  Address of the UDP receiver for broadcasting messages (default=localhost)
  --udp-port UDP_PORT  Port of the UDP receiver (default=57142)
  --fwd-fixed          Forward UDP to fixed target address/port
  --fwd-addr FWD_ADDR  Address of the UDP target for messages (default=localhost)
  --fwd-port FWD_PORT  Port of the UDP target (default=57143)
  --addr ADDR          WebSocket address to listen (default=0.0.0.0)
  --port PORT          WebSocket port to listen (default=8765)
  --broadcast          Enable UDP broadcasting
  --quiet              No verbose output
```

If the `fwd-fixed` option is not given (default behavior),
the server expects binary messages following the format:

**address_length**(uint32)**address**(string)**port**(uint32)**data**

* _address_length_ is an integer representing the total length of the address
* _address_ the address where to forward the data as a string (example: localhost)
* _port_ as an integer
* _data_ the original message data

For example, to send the message `hello world` to `localhost:57120`, one would send:

`b'\x09\x00\x00\x00localhost\x20\xdf\x00\x00hello, world'`

The first 4 bytes `b'\x09\x00\x00\x00` represents 9, then comes `b'localhost'` and lastly `b'\x20\xdf\x00\x00'` for 57120. Whatever comes after this is forwarded.


If the `fwd-fixed` option is given, the original message data will be forwarded unaltered.
