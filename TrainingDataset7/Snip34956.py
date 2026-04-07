def test_build_suite_shuffling(self):
        # These will result in unittest.loader._FailedTest instances rather
        # than TestCase objects, but they are sufficient for testing.
        labels = ["label1", "label2", "label3", "label4"]
        cases = [
            ({}, ["label1", "label2", "label3", "label4"]),
            ({"reverse": True}, ["label4", "label3", "label2", "label1"]),
            ({"shuffle": 8}, ["label4", "label1", "label3", "label2"]),
            ({"shuffle": 8, "reverse": True}, ["label2", "label3", "label1", "label4"]),
        ]
        for kwargs, expected in cases:
            with self.subTest(kwargs=kwargs):
                # Prevent writing the seed to stdout.
                runner = DiscoverRunner(**kwargs, verbosity=0)
                tests = runner.build_suite(test_labels=labels)
                # The ids have the form "unittest.loader._FailedTest.label1".
                names = [test.id().split(".")[-1] for test in tests]
                self.assertEqual(names, expected)