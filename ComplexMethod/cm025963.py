def _collect_errors(
    job: supervisor_jobs.Job, child_job_name: str, grandchild_job_name: str
) -> dict[str, list[tuple[str, str]]]:
    """Collect errors from a job's grandchildren."""
    errors: dict[str, list[tuple[str, str]]] = {}
    for child_job in job.child_jobs:
        if child_job.name != child_job_name:
            continue
        for grandchild in child_job.child_jobs:
            if (
                grandchild.name != grandchild_job_name
                or not grandchild.errors
                or not grandchild.reference
            ):
                continue
            errors[grandchild.reference] = [
                (error.type, error.message) for error in grandchild.errors
            ]
    return errors