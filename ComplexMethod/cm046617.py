def apply_update(job: Job, update: ParsedUpdate) -> None:
    if update.stage is not None:
        job.stage = update.stage
    if update.current_column is not None:
        job.current_column = update.current_column
        if (
            update.stage == STAGE_GENERATING
            and update.current_column not in job._seen_generation_columns
        ):
            job._seen_generation_columns.append(update.current_column)
    if update.rows is not None:
        job.rows = update.rows
    if update.cols is not None:
        job.cols = update.cols
    if update.progress is not None:
        job.column_progress = update.progress
        if (
            job.current_column
            and update.progress.done is not None
            and update.progress.total is not None
            and update.progress.total > 0
            and update.progress.done >= update.progress.total
            and job.current_column not in job.completed_columns
        ):
            job.completed_columns.append(job.current_column)
        job.progress = _compute_overall_progress(job, update.progress)
    if update.batch_idx is not None:
        job.batch.idx = update.batch_idx
    if update.batch_total is not None:
        job.batch.total = update.batch_total

    if update.stage in USAGE_RESET_STAGES:
        # usage summary is a short block so we reset once we move into the next stage.
        job._in_usage_summary = False

    if update.usage_section_start is not None:
        job._in_usage_summary = update.usage_section_start
        if update.usage_section_start:
            job._current_usage_model = None

    if not job._in_usage_summary:
        return

    if update.usage_model is not None:
        name = update.usage_model.strip().strip("'").strip('"')
        job._current_usage_model = name
        if name not in job.model_usage:
            job.model_usage[name] = ModelUsage(model = name)

    if job._current_usage_model is None:
        return

    usage = job.model_usage.get(job._current_usage_model)
    if usage is None:
        return

    if update.usage_input_tokens is not None:
        usage.input_tokens = update.usage_input_tokens
    if update.usage_output_tokens is not None:
        usage.output_tokens = update.usage_output_tokens
    if update.usage_total_tokens is not None:
        usage.total_tokens = update.usage_total_tokens
    if update.usage_tps is not None:
        usage.tps = update.usage_tps
    if update.usage_requests_success is not None:
        usage.requests_success = update.usage_requests_success
    if update.usage_requests_failed is not None:
        usage.requests_failed = update.usage_requests_failed
    if update.usage_requests_total is not None:
        usage.requests_total = update.usage_requests_total
    if update.usage_rpm is not None:
        usage.rpm = update.usage_rpm