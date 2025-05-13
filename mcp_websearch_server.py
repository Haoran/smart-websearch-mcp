# mcp_websearch_server.py

import os
import json
import logging
import asyncio
from typing import Any, List
import websockets
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from anthropic import Anthropic
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Log setting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server instance
app = Server("smart_web_search-mcp")

# Get API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY environment variable is not set")
    raise ValueError("ANTHROPIC_API_KEY is required")

# Initialize Anthropic client
try:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("Anthropic client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Anthropic client: {e}")
    raise

async def search_with_claude(query: str) -> str:
    """Use Claude's built-in web search to search"""
    logger.info(f"Searching for: {query}")
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": f"Please search for the following content and provide detailed search results: {query}"
                }
            ],
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                }
            ],
            system="Use the web_search tool to search for information and return detailed search results. Ensure it includes the latest information."
        )
        
        # Extract search results
        search_results = []
        for content_block in response.content:
            if content_block.type == "text":
                search_results.append(content_block.text)
            elif content_block.type == "tool_use" and content_block.name == "web_search":
                try:
                    tool_input = json.loads(content_block.input) if isinstance(content_block.input, str) else content_block.input
                    actual_query = tool_input.get('query', '')
                    logger.info(f"Actual search query: {actual_query}")
                except Exception as e:
                    logger.error(f"Error parsing tool input: {e}")
        
        result = "\n".join(search_results) if search_results else "No related search results found."
        logger.info(f"Search completed successfully, result length: {len(result)}")
        return result
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Search failed: {str(e)}"

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    logger.info("list_tools called")
    return [
        Tool(
            name="smart_web_search",
            description="Searches the web and provides concise, insight-rich summaries from live data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The content to search, can be any question or topic"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"call_tool: {name} with arguments: {arguments}")
    
    if name != "smart_web_search":
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    if not isinstance(arguments, dict) or "query" not in arguments:
        error_msg = f"Invalid arguments for smart_web_search: {arguments}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    query = arguments["query"]
    result = await search_with_claude(query)
    
    return [TextContent(type="text", text=result)]

# WebSocket handler
async def handle_websocket(websocket):
    logger.info(f"New WebSocket connection from {websocket.remote_address}")
    
    async for message in websocket:
        try:
            request = json.loads(message)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.info(f"Received method: {method}")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "1.0.0",
                        "serverInfo": {
                            "name": "smart_web_search-mcp",
                            "version": "1.0.0"
                        },
                        "capabilities": {
                            "tools": {},
                            "streaming": True
                        }
                    },
                    "id": request_id
                }
            
            elif method == "tools/list":
                # 注意：这里调用的是 async 函数
                tools = await list_tools()
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": [tool.dict() for tool in tools]
                    },
                    "id": request_id
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                # 注意：call_tool 只需要两个参数
                results = await call_tool(tool_name, arguments)
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": result.text} for result in results]
                    },
                    "id": request_id
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
            
            await websocket.send(json.dumps(response))
            logger.info(f"Sent response for method: {method}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request.get("id") if 'request' in locals() else None
            }
            await websocket.send(json.dumps(error_response))

async def main():
    """Run WebSocket MCP Server"""
    logger.info("Starting WebSocket MCP Server...")
    
    host = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    port = int(os.getenv("WEBSOCKET_PORT", "8765"))
    
    async with websockets.serve(handle_websocket, host, port):
        logger.info(f"WebSocket server listening on {host}:{port}")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        import sys
        sys.exit(1)