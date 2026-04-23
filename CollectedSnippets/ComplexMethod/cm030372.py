def _find_tests(self, start_dir, pattern, namespace=False):
        """Used by discovery. Yields test suites it loads."""
        # Handle the __init__ in this package
        name = self._get_name_from_path(start_dir)
        # name is '.' when start_dir == top_level_dir (and top_level_dir is by
        # definition not a package).
        if name != '.' and name not in self._loading_packages:
            # name is in self._loading_packages while we have called into
            # loadTestsFromModule with name.
            tests, should_recurse = self._find_test_path(
                start_dir, pattern, namespace)
            if tests is not None:
                yield tests
            if not should_recurse:
                # Either an error occurred, or load_tests was used by the
                # package.
                return
        # Handle the contents.
        paths = sorted(os.listdir(start_dir))
        for path in paths:
            full_path = os.path.join(start_dir, path)
            tests, should_recurse = self._find_test_path(
                full_path, pattern, False)
            if tests is not None:
                yield tests
            if should_recurse:
                # we found a package that didn't use load_tests.
                name = self._get_name_from_path(full_path)
                self._loading_packages.add(name)
                try:
                    yield from self._find_tests(full_path, pattern, False)
                finally:
                    self._loading_packages.discard(name)