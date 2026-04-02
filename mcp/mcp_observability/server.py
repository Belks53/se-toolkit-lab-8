"""Stdio MCP server exposing observability tools for VictoriaLogs and VictoriaTraces."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("observability")

# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchArgs(BaseModel):
    query: str = Field(
        default="",
        description="LogsQL query string. Examples: 'error', '_stream:{service=\"backend\"}', 'level:error'",
    )
    start: str = Field(
        default="-1h",
        description="Start time for the search. Examples: '-1h', '-24h', '2024-01-01T00:00:00Z'",
    )
    end: str = Field(
        default="now",
        description="End time for the search. Use 'now' for current time.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of log entries to return (1-1000).",
    )


class _LogsErrorCountArgs(BaseModel):
    start: str = Field(
        default="-1h",
        description="Start of the time window. Examples: '-1h', '-24h'.",
    )
    end: str = Field(
        default="now",
        description="End of the time window. Use 'now' for current time.",
    )


class _TracesListArgs(BaseModel):
    service: str = Field(
        default="backend",
        description="Service name to filter traces. Examples: 'backend', 'otel-collector'.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of traces to return (1-100).",
    )
    start: str = Field(
        default="-1h",
        description="Start time for the search. Examples: '-1h', '-24h'.",
    )


class _TracesGetArgs(BaseModel):
    trace_id: str = Field(
        ...,
        description="The trace ID to fetch. This is a hex string like 'ce7db3d229254622491e6565903cfa6a'.",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text(data: Any) -> list[TextContent]:
    """Serialize data to a JSON text block."""
    if isinstance(data, (dict, list)):
        content = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        content = str(data)
    return [TextContent(type="text", text=content)]


def _parse_time(time_str: str) -> str:
    """Convert relative time to VictoriaLogs/VictoriaTraces format."""
    if time_str == "now":
        return "now"
    return time_str


# ---------------------------------------------------------------------------
# VictoriaLogs tools
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchArgs, logs_url: str) -> list[TextContent]:
    """Search logs using VictoriaLogs LogsQL API."""
    try:
        # Build the LogsQL query
        query = args.query if args.query else "error OR level:error"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # VictoriaLogs LogsQL query endpoint
            url = f"{logs_url}/select/logsql/query"
            params = {
                "query": query,
                "start": _parse_time(args.start),
                "end": _parse_time(args.end),
                "limit": args.limit,
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # VictoriaLogs returns newline-delimited JSON
            lines = response.text.strip().split("\n")
            results = []
            for line in lines:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        results.append({"raw": line})
            
            if not results:
                return _text({"message": "No logs found matching the query.", "count": 0})
            
            return _text({
                "count": len(results),
                "query": query,
                "time_range": {"start": args.start, "end": args.end},
                "logs": results[:50],  # Limit output for readability
            })
            
    except httpx.ConnectError as e:
        return _text({"error": f"Cannot connect to VictoriaLogs: {e}"})
    except httpx.HTTPStatusError as e:
        return _text({"error": f"HTTP error: {e.response.status_code} - {e.response.text}"})
    except Exception as e:
        return _text({"error": f"Error searching logs: {type(e).__name__}: {e}"})


async def _logs_error_count(args: _LogsErrorCountArgs, logs_url: str) -> list[TextContent]:
    """Count errors per service over a time window."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Query for error count by service
            query = 'level:error OR "error" OR "ERROR"'
            url = f"{logs_url}/select/logsql/query"
            params = {
                "query": query,
                "start": _parse_time(args.start),
                "end": _parse_time(args.end),
                "limit": 1000,
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            # Parse results and count by service
            lines = response.text.strip().split("\n")
            error_count = 0
            by_service: dict[str, int] = {}
            
            for line in lines:
                if line.strip():
                    error_count += 1
                    try:
                        entry = json.loads(line)
                        service = entry.get("_stream", {}).get("service", "unknown")
                        by_service[service] = by_service.get(service, 0) + 1
                    except json.JSONDecodeError:
                        by_service["unknown"] = by_service.get("unknown", 0) + 1
            
            return _text({
                "total_errors": error_count,
                "time_range": {"start": args.start, "end": args.end},
                "by_service": by_service,
            })
            
    except httpx.ConnectError as e:
        return _text({"error": f"Cannot connect to VictoriaLogs: {e}"})
    except Exception as e:
        return _text({"error": f"Error counting errors: {type(e).__name__}: {e}"})


# ---------------------------------------------------------------------------
# VictoriaTraces tools
# ---------------------------------------------------------------------------


async def _traces_list(args: _TracesListArgs, traces_url: str) -> list[TextContent]:
    """List recent traces for a service using Jaeger API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # VictoriaTraces Jaeger-compatible API
            url = f"{traces_url}/jaeger/api/traces"
            params = {
                "service": args.service,
                "limit": args.limit,
            }
            
            # Add time range if specified
            if args.start:
                # Convert relative time to microseconds timestamp
                params["start"] = args.start
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Jaeger API returns {"data": [...]}
            traces = data.get("data", [])
            
            if not traces:
                return _text({
                    "message": f"No traces found for service '{args.service}'.",
                    "service": args.service,
                })
            
            # Summarize traces
            trace_summaries = []
            for trace in traces[:20]:  # Limit for readability
                trace_id = trace.get("traceID", "unknown")
                spans = trace.get("spans", [])
                span_count = len(spans)
                
                # Get the root span for operation name
                operation = "unknown"
                duration = 0
                if spans:
                    # Find the earliest span
                    root_span = min(spans, key=lambda s: s.get("startTime", float("inf")))
                    operation = root_span.get("operationName", "unknown")
                    # Calculate total duration
                    start_times = [s.get("startTime", 0) for s in spans]
                    end_times = [s.get("startTime", 0) + s.get("duration", 0) for s in spans]
                    if start_times and end_times:
                        duration = max(end_times) - min(start_times)
                
                trace_summaries.append({
                    "trace_id": trace_id,
                    "operation": operation,
                    "span_count": span_count,
                    "duration_us": duration,
                    "duration_ms": round(duration / 1000, 2),
                })
            
            return _text({
                "service": args.service,
                "trace_count": len(traces),
                "traces": trace_summaries,
            })
            
    except httpx.ConnectError as e:
        return _text({"error": f"Cannot connect to VictoriaTraces: {e}"})
    except httpx.HTTPStatusError as e:
        return _text({"error": f"HTTP error: {e.response.status_code} - {e.response.text}"})
    except Exception as e:
        return _text({"error": f"Error listing traces: {type(e).__name__}: {e}"})


async def _traces_get(args: _TracesGetArgs, traces_url: str) -> list[TextContent]:
    """Fetch a specific trace by ID."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{traces_url}/jaeger/api/traces/{args.trace_id}"
            
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Jaeger API returns {"data": [trace]}
            traces = data.get("data", [])
            
            if not traces:
                return _text({"error": f"Trace {args.trace_id} not found."})
            
            trace = traces[0]
            
            # Build a summary of the trace
            spans = trace.get("spans", [])
            span_summaries = []
            
            for span in sorted(spans, key=lambda s: s.get("startTime", 0)):
                span_info = {
                    "span_id": span.get("spanID", "unknown"),
                    "operation": span.get("operationName", "unknown"),
                    "service": span.get("process", {}).get("serviceName", "unknown"),
                    "duration_us": span.get("duration", 0),
                    "duration_ms": round(span.get("duration", 0) / 1000, 2),
                    "start_time": span.get("startTime", 0),
                }
                
                # Check for errors in tags
                for tag in span.get("tags", []):
                    if tag.get("key") == "error" and tag.get("value"):
                        span_info["error"] = True
                        span_info["error_message"] = str(tag.get("value"))
                
                span_summaries.append(span_info)
            
            # Calculate total duration
            if spans:
                start_times = [s.get("startTime", 0) for s in spans]
                end_times = [s.get("startTime", 0) + s.get("duration", 0) for s in spans]
                total_duration = max(end_times) - min(start_times)
            else:
                total_duration = 0
            
            return _text({
                "trace_id": args.trace_id,
                "span_count": len(spans),
                "total_duration_us": total_duration,
                "total_duration_ms": round(total_duration / 1000, 2),
                "spans": span_summaries,
            })
            
    except httpx.ConnectError as e:
        return _text({"error": f"Cannot connect to VictoriaTraces: {e}"})
    except httpx.HTTPStatusError as e:
        return _text({"error": f"HTTP error: {e.response.status_code} - {e.response.text}"})
    except Exception as e:
        return _text({"error": f"Error fetching trace: {type(e).__name__}: {e}"})


# ---------------------------------------------------------------------------
# Registry: tool name -> (input model, handler, Tool definition)
# ---------------------------------------------------------------------------

_Registry = tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]

_TOOLS: dict[str, _Registry] = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (
        model,
        handler,
        Tool(name=name, description=description, inputSchema=schema),
    )


# ---------------------------------------------------------------------------
# Global URLs (set in main())
# ---------------------------------------------------------------------------

_logs_url = "http://localhost:9428"
_traces_url = "http://localhost:10428"


def _logs_search_wrapper(args: _LogsSearchArgs) -> list[TextContent]:
    return asyncio.get_event_loop().run_until_complete(_logs_search(args, _logs_url))


def _logs_error_count_wrapper(args: _LogsErrorCountArgs) -> list[TextContent]:
    return asyncio.get_event_loop().run_until_complete(_logs_error_count(args, _logs_url))


def _traces_list_wrapper(args: _TracesListArgs) -> list[TextContent]:
    return asyncio.get_event_loop().run_until_complete(_traces_list(args, _traces_url))


def _traces_get_wrapper(args: _TracesGetArgs) -> list[TextContent]:
    return asyncio.get_event_loop().run_until_complete(_traces_get(args, _traces_url))


# Register tools
_register(
    "logs_search",
    "Search logs in VictoriaLogs using LogsQL. Use for finding errors, debugging issues, or analyzing system behavior. Returns log entries with timestamps, service names, and log content.",
    _LogsSearchArgs,
    _logs_search_wrapper,
)

_register(
    "logs_error_count",
    "Count errors per service over a time window. Use to get a quick overview of system health and identify which services are having issues.",
    _LogsErrorCountArgs,
    _logs_error_count_wrapper,
)

_register(
    "traces_list",
    "List recent traces for a service. Shows trace IDs, operations, span counts, and durations. Use to explore request patterns and find slow operations.",
    _TracesListArgs,
    _traces_list_wrapper,
)

_register(
    "traces_get",
    "Fetch a specific trace by ID. Shows all spans in the trace with their durations and any errors. Use to debug a specific request flow.",
    _TracesGetArgs,
    _traces_get_wrapper,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await asyncio.get_event_loop().run_in_executor(None, lambda: handler(args))
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main(logs_url: str | None = None, traces_url: str | None = None) -> None:
    global _logs_url, _traces_url
    _logs_url = logs_url or os.environ.get("VICTORIALOGS_URL", "http://localhost:9428")
    _traces_url = traces_url or os.environ.get("VICTORIATRACES_URL", "http://localhost:10428")
    
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
