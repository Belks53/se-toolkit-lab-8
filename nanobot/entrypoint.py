#!/usr/bin/env python3
"""
Entrypoint for nanobot Docker deployment.

Resolves environment variables into config.json at runtime,
then launches nanobot gateway.
"""

import json
import os
import sys
from pathlib import Path


def resolve_config():
    """Load config.json, inject env vars, write resolved config."""
    config_path = Path("/app/nanobot/config.json")
    resolved_path = Path("/app/nanobot/config.resolved.json")
    workspace_path = Path("/app/nanobot/workspace")

    if not config_path.exists():
        print(f"Error: Config not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Resolve LLM provider config from env vars
    if "providers" in config and "custom" in config["providers"]:
        if api_key := os.environ.get("QWEN_CODE_API_KEY"):
            config["providers"]["custom"]["apiKey"] = api_key
        if api_base := os.environ.get("QWEN_CODE_API_BASE_URL"):
            config["providers"]["custom"]["apiBase"] = api_base

    # Resolve MCP server env vars
    if "tools" in config and "mcpServers" in config["tools"]:
        if "lms" in config["tools"]["mcpServers"]:
            lms_config = config["tools"]["mcpServers"]["lms"]
            if "env" in lms_config:
                if backend_url := os.environ.get("NANOBOT_LMS_BACKEND_URL"):
                    lms_config["env"]["NANOBOT_LMS_BACKEND_URL"] = backend_url
                if api_key := os.environ.get("NANOBOT_LMS_API_KEY"):
                    lms_config["env"]["NANOBOT_LMS_API_KEY"] = api_key

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    return str(resolved_path), str(workspace_path)


if __name__ == "__main__":
    # Add MCP server to Python path
    mcp_path = Path("/app/mcp")
    if mcp_path.exists() and str(mcp_path) not in sys.path:
        sys.path.insert(0, str(mcp_path))

    resolved_config, workspace = resolve_config()

    # Launch nanobot gateway using the CLI module
    from nanobot.cli.commands import gateway as gateway_cmd
    
    # Call the gateway function directly with the resolved config
    gateway_cmd(
        port=None,
        workspace=workspace,
        verbose=False,
        config=resolved_config
    )
