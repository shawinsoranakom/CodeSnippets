def main():
  parser = argparse.ArgumentParser(description="Fetch CI results from GitHub Actions and Jenkins")
  parser.add_argument("--wait", action="store_true", help="Wait for CI to complete")
  parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds (default: 1800)")
  parser.add_argument("-o", "--output", default="ci_results.md", help="Output file (default: ci_results.md)")
  parser.add_argument("--branch", help="Branch to check (default: current branch)")
  parser.add_argument("--commit", help="Commit SHA to check (default: HEAD)")
  args = parser.parse_args()

  branch, commit = get_git_info()
  branch = args.branch or branch
  commit = args.commit or commit
  print(f"Fetching CI results for {branch} @ {commit[:7]}")

  start_time = time.monotonic()
  while True:
    gh_status, gh_run_id = get_github_actions_status(commit)
    jenkins_status = get_jenkins_status(branch, commit) if branch != "HEAD" else None

    if not args.wait or is_complete(gh_status, jenkins_status):
      break

    elapsed = time.monotonic() - start_time
    if elapsed >= args.timeout:
      print(f"Timeout after {int(elapsed)}s")
      break

    print(f"CI still running, waiting {POLL_INTERVAL}s... ({int(elapsed)}s elapsed)")
    time.sleep(POLL_INTERVAL)

  content = format_markdown(gh_status, gh_run_id, jenkins_status, commit, branch)
  with open(args.output, "w") as f:
    f.write(content)
  print(f"Results written to {args.output}")