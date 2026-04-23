def _augment_frames(frames: list[_Frame]) -> int:
    """
    Augment a list of frames with FX debug information. For each frame corresponding
    to an FX-generated Python file, this function attaches additional FX node
    metadata (op, name, target, and original trace).

    Args:
        frames (list[_Frame]): List of frame dictionaries to augment

    Returns:
        int: The count of frames that were augmented.
    """
    from torch.fx.graph_module import FX_GRAPH_MODULE_FILE_PREFIX
    from torch.fx.traceback import _FX_METADATA_REGISTRY

    # Regex pattern to match FX generated files
    _FX_GENERATED_PATTERN = re.compile(
        rf"{re.escape(FX_GRAPH_MODULE_FILE_PREFIX)}.*\.py$"
    )

    count = 0

    for frame in frames:
        filename = frame.get("filename")
        lineno = frame.get("line")
        if not filename or not lineno:
            continue

        # Check if this looks like an FX generated file
        if not _FX_GENERATED_PATTERN.search(os.path.basename(filename)):
            continue

        metadata = _FX_METADATA_REGISTRY.get(filename)
        if metadata is None:
            continue

        lineno_map = metadata.get("lineno_map", {})
        node_metadata = metadata.get("node_metadata", {})
        prologue_start = metadata.get("prologue_start", 0)

        # Get the node index for this line
        node_idx = lineno_map.get(lineno - prologue_start)
        if node_idx is None:
            continue

        node_info = node_metadata.get(node_idx)
        if node_info is None:
            continue

        # Populate FX metadata fields
        frame["fx_node_op"] = node_info.get("op")
        frame["fx_node_name"] = node_info.get("name")
        frame["fx_node_target"] = str(node_info.get("target"))

        # Attach original stack trace if available
        original_trace = node_info.get("stack_trace")
        if original_trace:
            frame["fx_original_trace"] = original_trace

        count += 1

    return count