def _extract_result_envelope(stdout: str) -> tuple[str, ExecutionStructuredResult | None]:
    if not stdout:
        return "", None

    cleaned_lines: list[str] = []
    envelope: ExecutionStructuredResult | None = None

    for line in str(stdout).splitlines():
        if line.startswith(RESULT_MARKER_PREFIX):
            payload_b64 = line[len(RESULT_MARKER_PREFIX) :].strip()
            if not payload_b64:
                continue
            try:
                payload = base64.b64decode(payload_b64).decode("utf-8")
                envelope = ExecutionStructuredResult.model_validate_json(payload)
            except Exception as exc:
                logger.warning(f"Failed to decode structured result marker: {exc}")
                cleaned_lines.append(line)
            continue
        cleaned_lines.append(line)

    cleaned_stdout = "\n".join(cleaned_lines)
    if stdout.endswith("\n") and cleaned_stdout and not cleaned_stdout.endswith("\n"):
        cleaned_stdout += "\n"
    return cleaned_stdout, envelope