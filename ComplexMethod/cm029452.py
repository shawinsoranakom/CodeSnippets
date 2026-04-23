def summarize_function_call_output_payload(output_text: str) -> str:
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError:
        return (
            f"output_chars={len(output_text)} "
            f"preview='{truncate_for_log(output_text)}'"
        )

    if not isinstance(parsed, dict):
        return (
            f"output_type={type(parsed).__name__} "
            f"preview='{truncate_for_log(parsed)}'"
        )

    if "error" in parsed:
        error_text = ensure_str(parsed.get("error"))
        return f"error='{truncate_for_log(error_text)}'"

    summary_parts: list[str] = []

    content_text = ensure_str(parsed.get("content"))
    if content_text:
        summary_parts.append(f"content='{truncate_for_log(content_text, max_len=80)}'")

    details = parsed.get("details")
    if isinstance(details, dict):
        path = ensure_str(details.get("path"))

        diff_text = details.get("diff")
        if (not path) and isinstance(diff_text, str) and diff_text:
            for line in diff_text.splitlines():
                if line.startswith("--- "):
                    path = line.removeprefix("--- ").strip()
                    break

        if path:
            summary_parts.append(f"path={path}")

        edits = details.get("edits")
        if isinstance(edits, list):
            summary_parts.append(f"edits={len(edits)}")

        content_length = details.get("contentLength")
        if isinstance(content_length, int):
            summary_parts.append(f"content_length={content_length}")

        first_changed_line = details.get("firstChangedLine")
        if isinstance(first_changed_line, int):
            summary_parts.append(f"first_changed_line={first_changed_line}")

        if isinstance(diff_text, str) and diff_text:
            diff_lines = diff_text.count("\n")
            summary_parts.append(f"diff_chars={len(diff_text)}")
            summary_parts.append(f"diff_lines={diff_lines}")

    if not summary_parts:
        summary_parts.append(f"keys={sorted(parsed.keys())}")

    return " ".join(summary_parts)