def get_doctest_files(diff_with_last_commit: bool = False) -> list[str]:
    """
    Return a list of python and Markdown files where doc example have been modified between:

    - the current head and the main branch if `diff_with_last_commit=False` (default)
    - the current head and its parent commit otherwise.

    Returns:
        `List[str]`: The list of Python and Markdown files with a diff (files added or renamed are always returned, files
        modified are returned if the diff in the file is only in doctest examples).
    """
    repo = Repo(PATH_TO_REPO)

    test_files_to_run = []  # noqa
    if not diff_with_last_commit:
        print(f"main is at {repo.refs.main.commit}")
        print(f"Current head is at {repo.head.commit}")

        branching_commits = repo.merge_base(repo.refs.main, repo.head)
        for commit in branching_commits:
            print(f"Branching commit: {commit}")
        test_files_to_run = get_diff_for_doctesting(repo, repo.head.commit, branching_commits)
    else:
        print(f"main is at {repo.head.commit}")
        parent_commits = repo.head.commit.parents
        for commit in parent_commits:
            print(f"Parent commit: {commit}")
        test_files_to_run = get_diff_for_doctesting(repo, repo.head.commit, parent_commits)

    all_test_files_to_run = get_all_doctest_files()

    # Add to the test files to run any removed entry from "utils/not_doctested.txt".
    new_test_files = get_new_doctest_files(repo, repo.head.commit, repo.refs.main.commit)
    test_files_to_run = list(set(test_files_to_run + new_test_files))

    # Do not run slow doctest tests on CircleCI
    with open("utils/slow_documentation_tests.txt") as fp:
        slow_documentation_tests = set(fp.read().strip().split("\n"))
    test_files_to_run = [
        x for x in test_files_to_run if x in all_test_files_to_run and x not in slow_documentation_tests
    ]

    # Make sure we did not end up with a test file that was removed
    test_files_to_run = [f for f in test_files_to_run if (PATH_TO_REPO / f).exists()]

    return sorted(test_files_to_run)