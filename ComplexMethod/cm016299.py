def get_jobs_with_sync_tag(
    job: dict[str, Any],
) -> tuple[str, str, dict[str, Any]] | None:
    sync_tag = job.get("with", {}).get("sync-tag")
    if sync_tag is None:
        return None

    # remove the "if" field, which we allow to be different between jobs
    # (since you might have different triggering conditions on pull vs.
    # trunk, say.)
    if "if" in job:
        del job["if"]

    # same is true for ['with']['test-matrix']
    if "test-matrix" in job.get("with", {}):
        del job["with"]["test-matrix"]
    # and ['with']['tests-to-include'], since dispatch filters differ
    if "tests-to-include" in job.get("with", {}):
        del job["with"]["tests-to-include"]
    # and ['with']['build-environment'], since GPU-specific suffixes differ for ROCm
    if (
        "build-environment" in job.get("with", {})
        and "rocm" in job["with"]["build-environment"]
    ):
        del job["with"]["build-environment"]
    # and ['name'], since ROCm jobs append a GPU-specific suffix to the job name
    if "name" in job and "rocm" in job.get("name", ""):
        del job["name"]

    # normalize needs: remove helper job-filter so comparisons ignore it
    needs = job.get("needs")
    if needs:
        needs_list = [needs] if isinstance(needs, str) else list(needs)
        needs_list = [n for n in needs_list if n != "job-filter"]
        if not needs_list:
            job.pop("needs", None)
        elif len(needs_list) == 1:
            job["needs"] = needs_list[0]
        else:
            job["needs"] = needs_list

    return (sync_tag, job_id, job)