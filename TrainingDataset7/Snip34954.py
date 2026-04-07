def test_reverse(self):
        """
        Reverse should reorder tests while maintaining the grouping specified
        by ``DiscoverRunner.reorder_by``.
        """
        runner = DiscoverRunner(reverse=True, verbosity=0)
        suite = runner.build_suite(
            test_labels=("test_runner_apps.sample", "test_runner_apps.simple")
        )
        self.assertIn(
            "test_runner_apps.simple",
            next(iter(suite)).id(),
            msg="Test labels should be reversed.",
        )
        suite = runner.build_suite(test_labels=("test_runner_apps.simple",))
        suite = tuple(suite)
        self.assertIn(
            "DjangoCase", suite[0].id(), msg="Test groups should not be reversed."
        )
        self.assertIn(
            "SimpleCase", suite[4].id(), msg="Test groups order should be preserved."
        )
        self.assertIn(
            "DjangoCase2", suite[0].id(), msg="Django test cases should be reversed."
        )
        self.assertIn(
            "SimpleCase2", suite[4].id(), msg="Simple test cases should be reversed."
        )
        self.assertIn(
            "UnittestCase2",
            suite[8].id(),
            msg="Unittest test cases should be reversed.",
        )
        self.assertIn(
            "test_2", suite[0].id(), msg="Methods of Django cases should be reversed."
        )
        self.assertIn(
            "test_2", suite[4].id(), msg="Methods of simple cases should be reversed."
        )
        self.assertIn(
            "test_2", suite[9].id(), msg="Methods of unittest cases should be reversed."
        )