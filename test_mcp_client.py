#!/usr/bin/env python3
"""
MCP WebSocket Test Client
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPWebSocketClient:
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.websocket = None
        
    async def connect(self):
        """Connect to the WebSocket server"""
        logger.info(f"Connecting to {self.websocket_url}...")
        self.websocket = await websockets.connect(self.websocket_url)
        logger.info("Connected successfully!")
        
    async def send_request(self, method, params=None):
        """Send a JSON-RPC request to the server"""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def test_connection(self):
        """Test basic connection and list tools"""
        try:
            # Test 1: Initialize
            logger.info("\n=== Test 1: Initialize ===")
            init_response = await self.send_request("initialize", {
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            })
            logger.info(f"Initialize response: {init_response}")
            
            # Test 2: List tools
            logger.info("\n=== Test 2: List Tools ===")
            tools_response = await self.send_request("tools/list")
            logger.info(f"Available tools: {tools_response}")
            
            # Test 3: Call smart_web_search
            logger.info("\n=== Test 3: Call smart_web_search ===")
            search_response = await self.send_request("tools/call", {
                "name": "smart_web_search",
                "arguments": {
                    "query": "What is MCP protocol?"
                }
            })
            logger.info(f"Search response: {search_response}")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
        finally:
            await self.close()
    
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Connection closed")

async def main():
    host = os.getenv('MCP_SERVER_HOST', 'localhost')

    # EC2 instance public IP
    EC2_PUBLIC_IP = host
    WEBSOCKET_URL = f"ws://{EC2_PUBLIC_IP}:8765"
    
    client = MCPWebSocketClient(WEBSOCKET_URL)
    
    try:
        await client.connect()
        await client.test_connection()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())