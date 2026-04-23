def format_markdown(gh_status, gh_run_id, jenkins_status, commit_sha, branch):
  lines = ["# CI Results", "",
           f"**Branch**: {branch}",
           f"**Commit**: {commit_sha[:7]}",
           f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]

  lines.extend(["## GitHub Actions", "", "| Job | Status | Duration |", "|-----|--------|----------|"])
  failed_gh_jobs = []
  if gh_status:
    for job_name, job in gh_status.items():
      icon = status_icon(job["status"], job.get("conclusion"))
      conclusion = job.get("conclusion") or job["status"]
      lines.append(f"| {job_name} | {icon} {conclusion} | {job.get('duration', '')} |")
      if job.get("conclusion") == "failure":
        failed_gh_jobs.append((job_name, job.get("id")))
  else:
    lines.append("| - | No workflow runs found | |")

  lines.extend(["", "## Jenkins", "", "| Stage | Status |", "|-------|--------|"])
  failed_jenkins_stages = []
  if jenkins_status:
    stages = jenkins_status.get("stages", [])
    if stages:
      for stage in stages:
        icon = ":white_check_mark:" if stage["status"] == "SUCCESS" else (
          ":x:" if stage["status"] == "FAILED" else ":hourglass:")
        lines.append(f"| {stage['name']} | {icon} {stage['status'].lower()} |")
        if stage["status"] == "FAILED":
          failed_jenkins_stages.append(stage["name"])
      # Show overall build status if still in progress
      if jenkins_status["in_progress"]:
        lines.append("| (build in progress) | :hourglass: in_progress |")
    else:
      icon = ":hourglass:" if jenkins_status["in_progress"] else (
        ":white_check_mark:" if jenkins_status["result"] == "SUCCESS" else ":x:")
      status = "in progress" if jenkins_status["in_progress"] else (jenkins_status["result"] or "unknown")
      lines.append(f"| #{jenkins_status['number']} | {icon} {status.lower()} |")
    if jenkins_status.get("url"):
      lines.append(f"\n[View build]({jenkins_status['url']})")
  else:
    lines.append("| - | No builds found for branch |")

  if failed_gh_jobs or failed_jenkins_stages:
    lines.extend(["", "## Failure Logs", ""])

  for job_name, job_id in failed_gh_jobs:
    lines.append(f"### GitHub Actions: {job_name}")
    log = get_github_job_log(gh_run_id, job_id)
    lines.extend(["", "```", log, "```", ""])

  for stage_name in failed_jenkins_stages:
    lines.append(f"### Jenkins: {stage_name}")
    log = get_jenkins_log(jenkins_status["url"])
    lines.extend(["", "```", log, "```", ""])

  return "\n".join(lines) + "\n"