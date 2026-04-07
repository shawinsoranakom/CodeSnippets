def load_tests_for_label(self, label, discover_kwargs):
        label_as_path = os.path.abspath(label)
        tests = None

        # If a module, or "module.ClassName[.method_name]", just run those.
        if not os.path.exists(label_as_path):
            with self.load_with_patterns():
                tests = self.test_loader.loadTestsFromName(label)
            if tests.countTestCases():
                return tests
        # Try discovery if "label" is a package or directory.
        is_importable, is_package = try_importing(label)
        if is_importable:
            if not is_package:
                return tests
        elif not os.path.isdir(label_as_path):
            if os.path.exists(label_as_path):
                assert tests is None
                raise RuntimeError(
                    f"One of the test labels is a path to a file: {label!r}, "
                    f"which is not supported. Use a dotted module name or "
                    f"path to a directory instead."
                )
            return tests

        kwargs = discover_kwargs.copy()
        if os.path.isdir(label_as_path) and not self.top_level:
            kwargs["top_level_dir"] = find_top_level(label_as_path)

        with self.load_with_patterns():
            tests = self.test_loader.discover(start_dir=label, **kwargs)

        # Make unittest forget the top-level dir it calculated from this run,
        # to support running tests from two different top-levels.
        self.test_loader._top_level_dir = None
        return tests