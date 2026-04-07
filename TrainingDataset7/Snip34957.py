def test_overridable_get_test_runner_kwargs(self):
        self.assertIsInstance(DiscoverRunner().get_test_runner_kwargs(), dict)