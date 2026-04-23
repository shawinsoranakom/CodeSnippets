def _parse_sse_response(text: str) -> dict[str, Any]:
        """Parse an SSE (text/event-stream) response body into JSON-RPC data.

        MCP servers may return responses as SSE with format:
            event: message
            data: {"jsonrpc":"2.0","result":{...},"id":1}

        We extract the last `data:` line that contains a JSON-RPC response
        (i.e. has an "id" field), which is the reply to our request.
        """
        last_data: dict[str, Any] | None = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("data:"):
                payload = stripped[len("data:") :].strip()
                if not payload:
                    continue
                try:
                    parsed = json.loads(payload)
                    # Only keep JSON-RPC responses (have "id"), skip notifications
                    if isinstance(parsed, dict) and "id" in parsed:
                        last_data = parsed
                except (json.JSONDecodeError, ValueError):
                    continue
        if last_data is None:
            raise MCPClientError("No JSON-RPC response found in SSE stream")
        return last_data