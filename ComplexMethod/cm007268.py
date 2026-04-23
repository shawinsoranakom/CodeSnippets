async def get_build_results(flow_id: str) -> dict[str, Any]:
    """Get per-component build results from the last run of a flow.

    Returns each component's output data, validity status, and any errors.
    Use this to debug which component failed or inspect intermediate outputs.

    Args:
        flow_id: The flow UUID.
    """
    data = await _get_client().get(f"/monitor/builds?flow_id={flow_id}")
    builds = data.get("vertex_builds", {})

    # Flatten to a more agent-friendly format
    summary: dict[str, Any] = {}
    for comp_id, build_list in builds.items():
        if not build_list:
            continue
        latest = build_list[-1]  # most recent build
        entry: dict[str, Any] = {
            "valid": latest.get("valid", False),
            "timestamp": latest.get("timestamp", ""),
        }
        # Include output data if present
        build_data = latest.get("data", {})
        if build_data:
            # Extract the result outputs
            results = build_data.get("results", {})
            for output_name, output_val in results.items():
                if isinstance(output_val, dict) and "text" in output_val:
                    entry[f"output_{output_name}"] = output_val["text"]
                elif isinstance(output_val, str):
                    entry[f"output_{output_name}"] = output_val
        # Include error info from artifacts if build failed
        artifacts = latest.get("artifacts", {})
        if not latest.get("valid") and artifacts:
            entry["error"] = str(artifacts)
        summary[comp_id] = entry

    return {"flow_id": flow_id, "builds": summary}