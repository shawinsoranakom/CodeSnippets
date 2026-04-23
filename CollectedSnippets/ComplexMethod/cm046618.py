def _compute_overall_progress(job: Job, column_progress: Progress) -> Progress:
    if not job.rows:
        return column_progress

    total_rows = max(1, int(job.rows))
    current_done = 0 if column_progress.done is None else int(column_progress.done)
    current_done = max(0, min(current_done, total_rows))
    total_columns = max(1, int(job.progress_columns_total or 1))

    if job.current_column:
        job._column_done[job.current_column] = current_done

    if len(job._column_done) == 0:
        done = current_done
    else:
        sum_done = sum(
            max(0, min(value, total_rows)) for value in job._column_done.values()
        )
        done = int(sum_done / total_columns)

    prev_done = int(job.progress.done or 0)
    if done < prev_done:
        done = prev_done
    if done > total_rows:
        done = total_rows
    percent = (done / total_rows) * 100 if total_rows > 0 else 100.0
    prev_percent = float(job.progress.percent or 0.0)
    if percent < prev_percent:
        percent = prev_percent

    return Progress(
        done = done,
        total = total_rows,
        percent = percent,
        eta_sec = column_progress.eta_sec,
        rate = column_progress.rate,
        ok = column_progress.ok,
        failed = column_progress.failed,
    )