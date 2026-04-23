def get_node_source_info(n: torch.fx.Node) -> str:
    """Extract the innermost user source location from an FX node's stack trace."""
    st = n.meta.get("stack_trace", "") or getattr(n, "stack_trace", "")
    if not st:
        return ""
    trace_lines = st.strip().split("\n")
    last_file_idx = -1
    for i, line in enumerate(trace_lines):
        if line.strip().startswith("File "):
            last_file_idx = i
    if last_file_idx < 0:
        return ""
    file_line = trace_lines[last_file_idx].strip()
    code = ""
    if last_file_idx + 1 < len(trace_lines):
        code = trace_lines[last_file_idx + 1].strip()
    return f"{file_line}" + (f", code: {code}" if code else "")