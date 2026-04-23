async def run_flow(
    flow_id: str,
    input_value: str = "",
    input_type: str = "chat",
    output_type: str = "chat",
    tweaks: dict[str, Any] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Run a flow and return the output.

    Streams progress events (tokens, messages) when the client supports it.

    Args:
        flow_id: The flow UUID.
        input_value: Text to send to the flow's input component.
        input_type: Input type (default: "chat").
        output_type: Output type (default: "chat").
        tweaks: Override component params at runtime: {component_id: {param: value}}.
        ctx: MCP context for progress reporting (injected automatically).
    """
    request = {
        "input_value": input_value,
        "input_type": input_type,
        "output_type": output_type,
        "tweaks": tweaks or {},
    }
    client = _get_client()

    result: dict[str, Any] = {}
    token_count = 0
    async for event in client.stream_post(f"/run/{flow_id}?stream=true", json_data=request):
        event_type = event.get("event", "")
        data = event.get("data", {})

        if event_type == "token" and ctx is not None:
            token_count += 1
            chunk = data.get("chunk", "")
            await ctx.report_progress(token_count, message=chunk)

        elif event_type == "end":
            result = data.get("result", data)
            break

        elif event_type == "error":
            msg = data.get("error", "Flow execution failed")
            raise RuntimeError(msg)

    if not result:
        logger.warning("Streaming produced no result for flow %s, falling back to synchronous execution", flow_id)
        return await client.post(f"/run/{flow_id}", json_data=request, timeout=300.0)
    return result