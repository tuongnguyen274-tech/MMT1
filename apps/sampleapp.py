#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
app.sampleapp
~~~~~~~~~~~~~~~~~

"""

import sys
import os
import importlib.util
import json

import asyncio

from   daemon import AsynapRous

app = AsynapRous()

active_peers = []

@app.route('/login', methods=['POST', 'PUT'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[SampleApp] Logging in {} to {}".format(headers, body))
    # Check for Authorization or Cookie in the headers for authentication
    is_authenticated = False
    headers_str = str(headers).lower()
    if "authorization" in headers_str or "cookie" in headers_str:
        is_authenticated = True
    if is_authenticated:
        data = {"message": "Welcome to the RESTful TCP WebApp", "status": "authenticated"}
    else:
        data = {"message": "Unauthorized. Missing Authorization or Cookie headers.", "status": "unauthorized"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

@app.route("/echo", methods=["POST"])
def echo(headers="guest", body="anonymous"):
    print("[SampleApp] received body {}".format(body))

    try:
        message = json.loads(body)
        data = {"received": message }
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
        # Convert to JSON string
        json_str = json.dumps(data)
        return (json_str.encode("utf-8"))


@app.route('/hello', methods=['PUT', 'POST'])
async def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] **ASYNC** Hello in {} to {}".format(headers, body))
    data =  {"id": 1, "name": "Alice", "email": "alice@example.com"}

    # Convert to JSON string
    json_str = json.dumps(data)
    return (json_str.encode("utf-8"))

# CLIENT-SERVER TRACKER & P2P LOGIC
@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers="guest", body="anonymous"):
    """
    Tracker logic to register a new active peer.
    """
    print("[Tracker] Received connection request: {}".format(body))
    try:
        peer_info = json.loads(body)
        if peer_info not in active_peers:
            active_peers.append(peer_info)
        
        data = {"status": "success", "active_peers": active_peers}
        return json.dumps(data).encode("utf-8")
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON format"}
        return json.dumps(data).encode("utf-8")

async def send_async_http_post(ip, port, path, data_dict):
    """
    Helper to send non-blocking P2P HTTP POST requests using standard Python libraries.
    """
    try:
        reader, writer = await asyncio.open_connection(ip, int(port))
        payload = json.dumps(data_dict)
        request = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {ip}:{port}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"Connection: close\r\n\r\n"
            f"{payload}"
        )
        writer.write(request.encode('utf-8'))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print("[P2P Client] Failed to connect to {}:{}: {}".format(ip, port, e))

@app.route('/send-message', methods=['POST'])
async def send_message(headers="guest", body="anonymous"):
    """
    Triggered by the user to broadcast a message to all connected peers in the tracker.
    """
    print("[P2P Client] Initiating broadcast to all peers...")
    try:
        message_data = json.loads(body)
        tasks = []
        for peer in active_peers:
            ip = peer.get("ip")
            port = peer.get("port")
            if ip and port:
                tasks.append(
                    asyncio.create_task(
                        send_async_http_post(ip, port, '/broadcast-peer', message_data)
                    )
                )
        
        # Execute all HTTP requests concurrently without blocking
        if tasks:
            await asyncio.gather(*tasks)
            
        data = {"status": "success", "message": "Broadcasted to peers"}
        return json.dumps(data).encode("utf-8")
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON format"}
        return json.dumps(data).encode("utf-8")

@app.route('/broadcast-peer', methods=['POST'])
async def broadcast_peer(headers="guest", body="anonymous"):
    """
    P2P logic to receive a broadcasted message from another peer.
    """
    try:
        message_data = json.loads(body)
        print("\n>>> [Incoming P2P Chat] {}: {}\n".format(
            message_data.get('sender', 'Unknown'), 
            message_data.get('text', '')
        ))
        data = {"status": "received"}
        return json.dumps(data).encode("utf-8")
    except json.JSONDecodeError:
        data = {"error": "Invalid JSON"}
        return json.dumps(data).encode("utf-8")

def create_sampleapp(ip, port):
    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()

