"""Entry point for the observability MCP server."""

import asyncio
import os
import sys

from mcp_observability.server import main

if __name__ == "__main__":
    # Get URLs from environment or command line
    logs_url = os.environ.get("VICTORIALOGS_URL", "http://localhost:9428")
    traces_url = os.environ.get("VICTORIATRACES_URL", "http://localhost:10428")
    
    if len(sys.argv) > 1:
        logs_url = sys.argv[1]
    if len(sys.argv) > 2:
        traces_url = sys.argv[2]
    
    asyncio.run(main(logs_url, traces_url))
