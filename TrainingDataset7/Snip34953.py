def test_duplicates_ignored(self):
        """
        Tests shouldn't be discovered twice when discovering on overlapping
        paths.
        """
        base_app = "forms_tests"
        sub_app = "forms_tests.field_tests"
        runner = DiscoverRunner(verbosity=0)
        with self.modify_settings(INSTALLED_APPS={"append": sub_app}):
            single = runner.build_suite([base_app]).countTestCases()
            dups = runner.build_suite([base_app, sub_app]).countTestCases()
        self.assertEqual(single, dups)