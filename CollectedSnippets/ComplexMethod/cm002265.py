def handle_suite(
    suite: str,
    test_root: Path,
    machine_type: str,
    dry_run: bool,
    tmp_cache: str = "",
    resume_at: str | None = None,
    only_in: list[str] | None = None,
    cpu_tests: bool = False,
    process_id: int = 1,
    total_processes: int = 1,
) -> None:
    """
    Handle execution of a complete test suite with advanced filtering and process distribution.
    Args:
        - suite (str): Name of the test suite to run (corresponds to a directory under test_root).
        - test_root (Path): Root directory containing all test suites.
        - machine_type (str): Machine/environment type for report naming and identification.
        - dry_run (bool): If True, only print commands without executing them.
        - tmp_cache (str, optional): Prefix for temporary cache directories. If empty, no temp cache is used.
        - resume_at (str, optional): Resume execution starting from this subdirectory name.
            Useful for restarting interrupted test runs. Defaults to None (run from the beginning).
        - only_in (list[str], optional): Only run tests in these specific subdirectories.
            Can include special values like IMPORTANT_MODELS. Defaults to None (run all tests).
        - cpu_tests (bool, optional): Whether to include CPU-only tests. Defaults to False.
        - process_id (int, optional): Current process ID for parallel execution (1-indexed). Defaults to 1.
        - total_processes (int, optional): Total number of parallel processes. Defaults to 1.
    """
    # Check path to suite
    full_path = test_root / suite
    if not full_path.exists():
        print(f"Test folder does not exist: {full_path}")
        return

    # Establish the list of subdir to go through
    subdirs = sorted(full_path.iterdir())
    subdirs = [s for s in subdirs if is_valid_test_dir(s)]
    if resume_at is not None:
        subdirs = [s for s in subdirs if s.name >= resume_at]
    if only_in is not None:
        subdirs = [s for s in subdirs if s.name in only_in]
    if subdirs and total_processes > 1:
        # This interleaves the subdirs / files. For instance for subdirs = [A, B, C, D, E] and 2 processes:
        # - script launcehd with `--processes 0 2` will run A, C, E
        # - script launcehd with `--processes 1 2` will run B, D
        subdirs = subdirs[process_id::total_processes]

    # If the subdir list is not empty, go through each
    if subdirs:
        for subdir in subdirs:
            run_pytest(suite, subdir, test_root, machine_type, dry_run, tmp_cache, cpu_tests)
    # Otherwise, launch pytest from the full path
    else:
        run_pytest(suite, full_path, test_root, machine_type, dry_run, tmp_cache, cpu_tests)