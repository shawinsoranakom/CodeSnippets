async def get_ci_results(
        credentials: GithubCredentials,
        repo: str,
        target: str | int,
        search_pattern: Optional[str] = None,
        check_name_filter: Optional[str] = None,
    ) -> dict:
        api = get_api(credentials, convert_urls=False)

        # Get the commit SHA
        commit_sha = await GithubGetCIResultsBlock.get_commit_sha(api, repo, target)

        # Get check runs for the commit
        check_runs_url = (
            f"https://api.github.com/repos/{repo}/commits/{commit_sha}/check-runs"
        )

        # Get all pages of check runs
        all_check_runs = []
        page = 1
        per_page = 100

        while True:
            response = await api.get(
                check_runs_url, params={"per_page": per_page, "page": page}
            )
            data = response.json()

            check_runs = data.get("check_runs", [])
            all_check_runs.extend(check_runs)

            if len(check_runs) < per_page:
                break
            page += 1

        # Filter by check name if specified
        if check_name_filter:
            import fnmatch

            filtered_runs = []
            for run in all_check_runs:
                if fnmatch.fnmatch(run["name"].lower(), check_name_filter.lower()):
                    filtered_runs.append(run)
            all_check_runs = filtered_runs

        # Get check run details with logs
        detailed_runs = []
        for run in all_check_runs:
            # Get detailed output including logs
            if run.get("output", {}).get("text"):
                # Already has output
                detailed_run = {
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run.get("conclusion"),
                    "started_at": run.get("started_at"),
                    "completed_at": run.get("completed_at"),
                    "html_url": run["html_url"],
                    "details_url": run.get("details_url"),
                    "output_title": run.get("output", {}).get("title"),
                    "output_summary": run.get("output", {}).get("summary"),
                    "output_text": run.get("output", {}).get("text"),
                    "annotations": [],
                }
            else:
                # Try to get logs from the check run
                detailed_run = {
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run.get("conclusion"),
                    "started_at": run.get("started_at"),
                    "completed_at": run.get("completed_at"),
                    "html_url": run["html_url"],
                    "details_url": run.get("details_url"),
                    "output_title": run.get("output", {}).get("title"),
                    "output_summary": run.get("output", {}).get("summary"),
                    "output_text": None,
                    "annotations": [],
                }

            # Get annotations if available
            if run.get("output", {}).get("annotations_count", 0) > 0:
                annotations_url = f"https://api.github.com/repos/{repo}/check-runs/{run['id']}/annotations"
                try:
                    ann_response = await api.get(annotations_url)
                    detailed_run["annotations"] = ann_response.json()
                except Exception:
                    pass

            detailed_runs.append(detailed_run)

        return {
            "check_runs": detailed_runs,
            "total_count": len(detailed_runs),
        }