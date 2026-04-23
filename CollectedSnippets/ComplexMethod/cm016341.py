def discover_tests(
    base_dir: Path = REPO_ROOT / "test",
    cpp_tests_dir: str | Path | None = None,
    blocklisted_patterns: list[str] | None = None,
    blocklisted_tests: list[str] | None = None,
    extra_tests: list[str] | None = None,
) -> list[str]:
    """
    Searches for all python files starting with test_ excluding one specified by patterns.
    If cpp_tests_dir is provided, also scan for all C++ tests under that directory. They
    are usually found in build/bin
    """

    def skip_test_p(name: str) -> bool:
        rc = False
        if blocklisted_patterns is not None:
            rc |= any(name.startswith(pattern) for pattern in blocklisted_patterns)
        if blocklisted_tests is not None:
            rc |= name in blocklisted_tests
        return rc

    # This supports symlinks, so we can link domain library tests to PyTorch test directory
    all_py_files = [
        Path(p) for p in glob.glob(f"{base_dir}/**/test_*.py", recursive=True)
    ]

    cpp_tests_dir = (
        f"{base_dir.parent}/{CPP_TEST_PATH}" if cpp_tests_dir is None else cpp_tests_dir
    )
    # CPP test files are located under pytorch/build/bin. Unlike Python test, C++ tests
    # are just binaries and could have any name, i.e. basic or atest
    all_cpp_files = [
        Path(p) for p in glob.glob(f"{cpp_tests_dir}/**/*", recursive=True)
    ]

    rc = [str(fname.relative_to(base_dir))[:-3] for fname in all_py_files]
    # Add the cpp prefix for C++ tests so that we can tell them apart
    rc.extend(
        [
            parse_test_module(f"{CPP_TEST_PREFIX}/{fname.relative_to(cpp_tests_dir)}")
            for fname in all_cpp_files
        ]
    )

    # Invert slashes on Windows
    if sys.platform == "win32":
        rc = [name.replace("\\", "/") for name in rc]
    rc = [test for test in rc if not skip_test_p(test)]
    if extra_tests is not None:
        rc += extra_tests
    return sorted(rc)