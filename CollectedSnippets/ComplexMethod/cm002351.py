def get_last_daily_ci_run(token, workflow_run_id=None, workflow_id=None, commit_sha=None):
    """Get the last completed workflow run id of the scheduled (daily) CI."""
    headers = None
    if token is not None:
        headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"}

    workflow_run = None
    if workflow_run_id is not None and workflow_run_id != "":
        workflow_run = requests.get(
            f"https://api.github.com/repos/huggingface/transformers/actions/runs/{workflow_run_id}", headers=headers
        ).json()
        return workflow_run

    workflow_runs = get_daily_ci_runs(token, workflow_id=workflow_id)
    for run in workflow_runs:
        if commit_sha in [None, ""] and run["status"] == "completed":
            workflow_run = run
            break
        # if `commit_sha` is specified, return the latest completed run with `workflow_run["head_sha"]` matching the specified sha.
        elif commit_sha not in [None, ""] and run["head_sha"] == commit_sha and run["status"] == "completed":
            workflow_run = run
            break

    return workflow_run