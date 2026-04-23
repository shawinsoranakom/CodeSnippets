def _extract_wrapper_body(code):
    """Extract and normalize the call method body from generated wrapper code.

    Strips noise (comments, assert_size_stride, del statements, args.clear())
    and normalizes triton kernel names, leaving just structural code:
    stream declarations, context switches, event ops, kernel calls, buffer allocations.
    """
    lines = code.split("\n")

    # Find the call function body
    call_start = None
    call_indent = 0
    for i, line in enumerate(lines):
        if "def call(" in line:
            call_indent = len(line) - len(line.lstrip())
            call_start = i + 1
            break

    if call_start is None:
        return ""

    # Extract body until next definition at same indent level or end
    body_lines = []
    for i in range(call_start, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if stripped:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= call_indent:
                break
        body_lines.append(line)

    # Filter out noise
    filtered = []
    for line in body_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if "assert_size_stride" in stripped:
            continue
        if stripped.startswith("del "):
            continue
        if "args.clear()" in stripped:
            continue
        # Strip inline comments (e.g., "# reuse")
        line = re.sub(r"\s+#\s.*", "", line)
        if not line.strip():
            continue
        filtered.append(line)

    if not filtered:
        return ""

    # Dedent
    min_indent = min(
        len(line) - len(line.lstrip()) for line in filtered if line.strip()
    )
    dedented = [line[min_indent:] for line in filtered]
    body = "\n".join(dedented)

    # Normalize triton kernel names
    body = re.sub(r"triton_\w+", "triton_kernel", body)

    return body