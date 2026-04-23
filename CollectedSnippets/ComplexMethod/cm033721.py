def filter_and_inject_targets(test: SanityTest, targets: c.Iterable[TestTarget]) -> list[TestTarget]:
        """Filter and inject targets based on test requirements and the given target list."""
        test_targets = list(targets)

        if not test.include_symlinks:
            # remove all symlinks unless supported by the test
            test_targets = [target for target in test_targets if not target.symlink]

        if not test.include_directories or not test.include_symlinks:
            # exclude symlinked directories unless supported by the test
            test_targets = [target for target in test_targets if not target.path.endswith(os.path.sep)]

        if test.include_directories:
            # include directories containing any of the included files
            test_targets += tuple(TestTarget(path, None, None, '') for path in paths_to_dirs([target.path for target in test_targets]))

            if not test.include_symlinks:
                # remove all directory symlinks unless supported by the test
                test_targets = [target for target in test_targets if not target.symlink]

        return test_targets