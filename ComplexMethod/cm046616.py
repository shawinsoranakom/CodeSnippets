def parse_log_message(msg: str) -> ParsedUpdate | None:
    m = _RE_SAMPLERS.search(msg)
    if m:
        return ParsedUpdate(
            stage = STAGE_SAMPLING,
            rows = int(m.group("rows")),
            cols = int(m.group("cols")),
        )

    if "Sorting column configs into a Directed Acyclic Graph" in msg:
        return ParsedUpdate(stage = STAGE_DAG)
    if "Running health checks for models" in msg:
        return ParsedUpdate(stage = STAGE_HEALTHCHECK)
    if "Preview generation in progress" in msg:
        return ParsedUpdate(stage = STAGE_PREVIEW)
    if "Creating Data Designer dataset" in msg:
        return ParsedUpdate(stage = STAGE_CREATE)
    if "Measuring dataset column statistics" in msg:
        return ParsedUpdate(stage = STAGE_PROFILING)

    m = _RE_COLCFG.search(msg)
    if m:
        col = m.group("col")
        return ParsedUpdate(stage = STAGE_COLUMN_CONFIG, current_column = col)

    m = _RE_PROCESSING_COL.search(msg)
    if m:
        col = m.group("col")
        return ParsedUpdate(stage = STAGE_GENERATING, current_column = col)

    m = _RE_PROGRESS.search(msg)
    if m:
        p = Progress(
            done = int(m.group("done")),
            total = int(m.group("total")),
            percent = float(m.group("pct")),
            ok = int(m.group("ok")),
            failed = int(m.group("failed")),
            rate = float(m.group("rate")),
            eta_sec = float(m.group("eta")),
        )
        return ParsedUpdate(stage = STAGE_GENERATING, progress = p)

    m = _RE_BATCH.search(msg)
    if m:
        return ParsedUpdate(
            stage = STAGE_BATCH,
            batch_idx = int(m.group("idx")),
            batch_total = int(m.group("total")),
        )

    if "Model usage summary" in msg:
        return ParsedUpdate(usage_section_start = True)

    m = _RE_USAGE_MODEL.search(msg)
    if m and "|-- model:" in msg:
        return ParsedUpdate(usage_model = str(m.group("model")).strip())

    m = _RE_USAGE_TOKENS.search(msg)
    if m:
        return ParsedUpdate(
            usage_input_tokens = int(m.group("input")),
            usage_output_tokens = int(m.group("output")),
            usage_total_tokens = int(m.group("total")),
            usage_tps = float(m.group("tps")),
        )

    m = _RE_USAGE_REQUESTS.search(msg)
    if m:
        return ParsedUpdate(
            usage_requests_success = int(m.group("success")),
            usage_requests_failed = int(m.group("failed")),
            usage_requests_total = int(m.group("total")),
            usage_rpm = float(m.group("rpm")),
        )

    return None