def can_reuse_whl(args: argparse.Namespace) -> tuple[bool, str]:
    if args.github_ref and any(
        args.github_ref.startswith(x)
        for x in [
            "refs/heads/release",
            "refs/tags/v",
            "refs/heads/nightly",
        ]
    ):
        print("Release branch, rebuild whl")
        return (False, "Release branch")

    if not check_changed_files(get_merge_base()):
        print("Cannot use old whl due to the changed files, rebuild whl")
        return (False, "Changed files not allowed")

    if check_labels_for_pr():
        print(f"Found {FORCE_REBUILD_LABEL} label on PR, rebuild whl")
        return (False, "Found FORCE_REBUILD_LABEL on PR")

    if check_issue_open():
        print("Issue #153759 is open, rebuild whl")
        return (False, "Issue #153759 is open")

    workflow_id = get_workflow_id(args.run_id)
    if workflow_id is None:
        print("No workflow ID found, rebuild whl")
        return (False, "No workflow ID found")

    if not find_old_whl(workflow_id, args.build_environment, get_merge_base()):
        print("No old whl found, rebuild whl")
        return (False, "No old whl found")
        # TODO: go backwards from merge base to find more runs

    return (True, "Found old whl")