def test_name_patterns(self):
        all_test_1 = [
            "DjangoCase1.test_1",
            "DjangoCase2.test_1",
            "SimpleCase1.test_1",
            "SimpleCase2.test_1",
            "UnittestCase1.test_1",
            "UnittestCase2.test_1",
        ]
        all_test_2 = [
            "DjangoCase1.test_2",
            "DjangoCase2.test_2",
            "SimpleCase1.test_2",
            "SimpleCase2.test_2",
            "UnittestCase1.test_2",
            "UnittestCase2.test_2",
        ]
        all_tests = sorted([*all_test_1, *all_test_2, "UnittestCase2.test_3_test"])
        for pattern, expected in [
            [["test_1"], all_test_1],
            [["UnittestCase1"], ["UnittestCase1.test_1", "UnittestCase1.test_2"]],
            [["*test"], ["UnittestCase2.test_3_test"]],
            [["test*"], all_tests],
            [["test"], all_tests],
            [["test_1", "test_2"], sorted([*all_test_1, *all_test_2])],
            [["test*1"], all_test_1],
        ]:
            with self.subTest(pattern):
                suite = DiscoverRunner(
                    test_name_patterns=pattern,
                    verbosity=0,
                ).build_suite(["test_runner_apps.simple"])
                self.assertEqual(expected, self.get_test_methods_names(suite))