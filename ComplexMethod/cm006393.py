def resolve_flow_path(flow_filename: str) -> tuple[Path, str]:
    """Resolve flow filename to path and determine type.

    Supports both explicit extensions (.json, .py) and auto-detection.
    Priority: explicit extension > .py > .json

    Args:
        flow_filename: Name of the flow file (with or without extension).

    Returns:
        tuple[Path, str]: (resolved path, file type: "json" or "python")

    Raises:
        HTTPException: If flow file not found.
    """
    # Early rejection of path traversal sequences before any path construction.
    if ".." in flow_filename or "\\" in flow_filename:
        raise HTTPException(status_code=400, detail=f"Invalid flow filename: '{flow_filename}'")

    if flow_filename.endswith(".json"):
        flow_path = FLOWS_BASE_PATH / flow_filename
        _validate_path_within_base(flow_path)
        if flow_path.exists():
            return flow_path, "json"
        raise HTTPException(status_code=404, detail=f"Flow file '{flow_filename}' not found")

    if flow_filename.endswith(".py"):
        flow_path = FLOWS_BASE_PATH / flow_filename
        _validate_path_within_base(flow_path)
        if flow_path.exists():
            return flow_path, "python"
        raise HTTPException(status_code=404, detail=f"Flow file '{flow_filename}' not found")

    # Auto-detect: try Python first, then JSON (allows gradual migration)
    base_name = flow_filename.rsplit(".", 1)[0] if "." in flow_filename else flow_filename

    py_path = FLOWS_BASE_PATH / f"{base_name}.py"
    _validate_path_within_base(py_path)
    if py_path.exists():
        return py_path, "python"

    json_path = FLOWS_BASE_PATH / f"{base_name}.json"
    _validate_path_within_base(json_path)
    if json_path.exists():
        return json_path, "json"

    # Try without adding extension
    direct_path = FLOWS_BASE_PATH / flow_filename
    _validate_path_within_base(direct_path)
    if direct_path.exists():
        if direct_path.suffix == ".py":
            return direct_path, "python"
        return direct_path, "json"

    raise HTTPException(status_code=404, detail=f"Flow file '{flow_filename}' not found")