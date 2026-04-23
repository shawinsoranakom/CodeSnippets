def format_slack_message(failures_file, workflow_url, output_file=None):
    """
    Format extras smoke test results into Slack message components.

    Args:
        failures_file: Path to JSON file containing failure reports
        workflow_url: URL to the GitHub Actions workflow run
        output_file: Optional path to output file (defaults to GITHUB_ENV)

    Returns:
        Dictionary with title, message, and workflow_url
    """
    # Read failures
    with open(failures_file) as f:
        failures = json.load(f)

    if not failures:
        # Success case
        title = "Extras Smoke Test - All tests passed"
        message = "All extras installed successfully across all Python versions."
    else:
        # Failure case - group by Python version
        failures_by_python = {}
        for failure in failures:
            py_ver = failure.get("python_version", "unknown")
            extra = failure.get("extra", "unknown")

            if py_ver not in failures_by_python:
                failures_by_python[py_ver] = []
            failures_by_python[py_ver].append(extra)

        title = f"Extras Smoke Test Failed - {len(failures)} failure(s)"

        # Build failure details
        details = []
        for py_ver in sorted(failures_by_python.keys()):
            extras = failures_by_python[py_ver]
            extras_list = "\n".join([f"• `{extra}`" for extra in sorted(extras)])
            details.append(f"*Python {py_ver}*\n{extras_list}")

        message = "\n\n".join(details)

    # Determine output destination
    if output_file is None:
        output_file = os.environ.get("GITHUB_ENV")
        if not output_file:
            print("Error: GITHUB_ENV not set and no output file specified", file=sys.stderr)
            sys.exit(1)

    # Write environment variables
    with open(output_file, "a") as f:
        f.write(f"SLACK_TITLE={title}\n")
        f.write(f"SLACK_WORKFLOW_URL={workflow_url}\n")
        # Use heredoc for multiline message
        f.write("SLACK_MESSAGE<<EOF\n")
        f.write(f"{message}\n")
        f.write("EOF\n")

    return {"title": title, "message": message, "workflow_url": workflow_url}