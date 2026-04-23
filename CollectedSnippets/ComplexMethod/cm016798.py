def get_all_jobs(
    running: list,
    queued: list,
    history: dict,
    status_filter: Optional[list[str]] = None,
    workflow_id: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: Optional[int] = None,
    offset: int = 0
) -> tuple[list[dict], int]:
    """
    Get all jobs (running, pending, completed) with filtering and sorting.

    Args:
        running: List of currently running queue items
        queued: List of pending queue items
        history: Dict of history items keyed by prompt_id
        status_filter: List of statuses to include (from JobStatus.ALL)
        workflow_id: Filter by workflow ID
        sort_by: Field to sort by ('created_at', 'execution_duration')
        sort_order: 'asc' or 'desc'
        limit: Maximum number of items to return
        offset: Number of items to skip

    Returns:
        tuple: (jobs_list, total_count)
    """
    jobs = []

    if status_filter is None:
        status_filter = JobStatus.ALL

    if JobStatus.IN_PROGRESS in status_filter:
        for item in running:
            jobs.append(normalize_queue_item(item, JobStatus.IN_PROGRESS))

    if JobStatus.PENDING in status_filter:
        for item in queued:
            jobs.append(normalize_queue_item(item, JobStatus.PENDING))

    history_statuses = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
    requested_history_statuses = history_statuses & set(status_filter)
    if requested_history_statuses:
        for prompt_id, history_item in history.items():
            job = normalize_history_item(prompt_id, history_item)
            if job.get('status') in requested_history_statuses:
                jobs.append(job)

    if workflow_id:
        jobs = [j for j in jobs if j.get('workflow_id') == workflow_id]

    jobs = apply_sorting(jobs, sort_by, sort_order)

    total_count = len(jobs)

    if offset > 0:
        jobs = jobs[offset:]
    if limit is not None:
        jobs = jobs[:limit]

    return (jobs, total_count)