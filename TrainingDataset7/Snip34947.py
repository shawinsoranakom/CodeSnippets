def test_file_path(self):
        with change_cwd(".."):
            count = (
                DiscoverRunner(verbosity=0)
                .build_suite(
                    ["test_runner_apps/sample/"],
                )
                .countTestCases()
            )

        self.assertEqual(count, 5)