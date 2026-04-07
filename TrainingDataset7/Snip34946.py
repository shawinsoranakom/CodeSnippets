def test_loader_patterns_not_mutated_when_test_label_is_file_path(self):
        runner = DiscoverRunner(test_name_patterns=["test_sample"], verbosity=0)
        with change_cwd("."), change_loader_patterns(["UnittestCase1"]):
            with self.assertRaises(RuntimeError):
                runner.build_suite(["test_discover_runner.py"])
            self.assertEqual(runner.test_loader.testNamePatterns, ["UnittestCase1"])