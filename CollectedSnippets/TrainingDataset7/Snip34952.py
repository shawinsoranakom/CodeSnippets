def test_testcase_ordering(self):
        with change_cwd(".."):
            suite = DiscoverRunner(verbosity=0).build_suite(
                ["test_runner_apps/sample/"]
            )
            self.assertEqual(
                suite._tests[0].__class__.__name__,
                "TestDjangoTestCase",
                msg="TestDjangoTestCase should be the first test case",
            )
            self.assertEqual(
                suite._tests[1].__class__.__name__,
                "TestZimpleTestCase",
                msg="TestZimpleTestCase should be the second test case",
            )
            # All others can follow in unspecified order, including doctests
            self.assertIn(
                "DocTestCase", [t.__class__.__name__ for t in suite._tests[2:]]
            )