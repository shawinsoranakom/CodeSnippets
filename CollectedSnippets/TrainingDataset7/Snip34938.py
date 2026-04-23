def test_load_tests_for_label_file_path(self):
        with change_cwd("."):
            msg = (
                "One of the test labels is a path to a file: "
                "'test_discover_runner.py', which is not supported. Use a "
                "dotted module name or path to a directory instead."
            )
            with self.assertRaisesMessage(RuntimeError, msg):
                DiscoverRunner().load_tests_for_label("test_discover_runner.py", {})