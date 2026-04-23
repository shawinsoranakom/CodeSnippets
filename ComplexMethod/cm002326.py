def find_bad_commit(target_test, start_commit, end_commit):
    """Find (backward) the earliest commit between `start_commit` (inclusive) and `end_commit` (exclusive) at which `target_test` fails.

    Args:
        target_test (`str`): The test to check.
        start_commit (`str`): The latest commit (inclusive).
        end_commit (`str`): The earliest commit (exclusive).

    Returns:
        `dict`: A dict containing the info about the earliest commit at which `target_test` fails.
    """
    result = {
        "bad_commit": None,
        "status": None,
        "failure_at_workflow_commit": None,
        "failure_at_base_commit": None,
        "failure_at_bad_commit": None,
    }

    is_pr_ci = os.environ.get("GITHUB_EVENT_NAME") in ["issue_comment", "pull_request"]

    # For PR comment CI, we "assume" all tests at `end_commit` passed, so any failing test during a PR CI run is
    # "a new failing test", and we can perform more detailed checks with this script.
    # For "a failing tes at start_commit", we check the test against `end_commit` (run multiple times):
    #   - if all passing at end_commit: an actual new failing test at start_commit
    #   - if all failing at end_commit: get the failure message and compare it against the one from start_commit:
    #     - same failure message: not a new failing test --> don't report it
    #      - different failure message: kind of a new failing test --> need to report it
    #   - if both failing and passing at end_commit: mark it as flaky

    # check if `end_commit` fails the test
    failed_before, n_failed, n_passed, failure_at_base_commit = is_bad_commit(target_test, end_commit)
    # We only need one failure to conclude the test is flaky on the previous run with `end_commit`.
    # However, when running on CI, we need at least one failure and one pass to conclude.
    is_flaky_at_end_commit = ((not is_pr_ci) and n_failed > 0) or (is_pr_ci and n_failed > 0 and n_passed > 0)
    # `n_passed == 0` itself is not enough, as the test may not exist in the codebase at `end_commit`.
    is_failing_at_end_commit = failed_before and n_passed == 0

    if is_flaky_at_end_commit:
        result["status"] = (
            f"flaky: test both passed and failed during the check of the current run on the previous commit: {end_commit}"
        )
        return result

    elif (not is_pr_ci) and is_failing_at_end_commit:
        result["status"] = (
            f"flaky: test passed in the previous run (commit: {end_commit}) but failed (on the same commit) during the check of the current run."
        )
        return result

    # if there is no new commit (e.g. 2 different CI runs on the same commit):
    #   - failed once on `start_commit` but passed on `end_commit`, which are the same commit --> flaky (or something change externally) --> don't report
    if start_commit == end_commit:
        result["status"] = (
            f"flaky: test fails on the current CI run but passed in the previous run which is running on the same commit {end_commit}."
        )
        return result

    # Now, we are (almost) sure `target_test` is not failing at `end_commit`. (For a PR CI, it may fail at `end_commit`)
    # Check if `start_commit` fails the test.
    # **IMPORTANT** we only need one pass to conclude the test is flaky on the current run with `start_commit`!
    _, n_failed, n_passed, failure_at_workflow_commit = is_bad_commit(target_test, start_commit)
    if n_passed > 0:
        # failed on CI run, but not reproducible here --> don't report
        result["status"] = (
            f"flaky: test fails on the current CI run (commit: {start_commit}) but passes during the check."
        )
        return result

    # The test fails on `start_commit`, and
    #   - if the CI is run on PR: this block checks if the test also failed on `start_commit`.
    #   - otherwise: the test passed on `end_commit` --> an actual new failing test, this block is skipped.
    if is_pr_ci and failure_at_base_commit != "" and failure_at_workflow_commit != failure_at_base_commit:
        result["bad_commit"] = start_commit
        result["status"] = (
            f"test fails both on the current commit ({start_commit}) and the previous commit ({end_commit}), but with DIFFERENT error message!"
        )
        result["failure_at_workflow_commit"] = failure_at_workflow_commit
        result["failure_at_base_commit"] = failure_at_base_commit
        result["failure_at_bad_commit"] = failure_at_workflow_commit
        return result
    # Fail on both commits but with the same error message ==> don't include
    elif is_pr_ci and failure_at_workflow_commit == failure_at_base_commit:
        result["bad_commit"] = None
        result["status"] = (
            f"test fails both on the current commit ({start_commit}) and the previous commit ({end_commit}) with the SAME error message!"
        )
        result["failure_at_workflow_commit"] = failure_at_workflow_commit
        result["failure_at_base_commit"] = failure_at_base_commit
        result["failure_at_bad_commit"] = failure_at_workflow_commit
        return result

    # The test fails on `start_commit` but passed on `end_commit`.
    create_script(target_test=target_test)

    bash = f"""
git bisect reset
git bisect start --first-parent {start_commit} {end_commit}
git bisect run python3 target_script.py
"""

    with open("run_git_bisect.sh", "w") as fp:
        fp.write(bash.strip())

    bash_result = subprocess.run(
        ["bash", "run_git_bisect.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    print(bash_result.stdout)

    # This happens if running the script gives exit code < 0  or other issues
    if "error: bisect run failed" in bash_result.stderr:
        error_msg = f"Error when running git bisect:\nbash error: {bash_result.stderr}\nbash output:\n{bash_result.stdout}\nset `bad_commit` to `None`."
        print(error_msg)
        result["status"] = "git bisect failed"
        return result

    pattern = r"(.+) is the first bad commit"
    commits = re.findall(pattern, bash_result.stdout)

    bad_commit = None
    failure_at_bad_commit = ""
    if len(commits) > 0:
        bad_commit = commits[0]
        _, _, _, failure_at_bad_commit = is_bad_commit(target_test, bad_commit)

    print(f"Between `start_commit` {start_commit} and `end_commit` {end_commit}")
    print(f"bad_commit: {bad_commit}\n")

    result["bad_commit"] = bad_commit
    result["status"] = "git bisect found the bad commit."
    result["failure_at_workflow_commit"] = failure_at_workflow_commit
    result["failure_at_base_commit"] = failure_at_base_commit
    result["failure_at_bad_commit"] = failure_at_bad_commit
    return result