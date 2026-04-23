def test_run_as_non_django_module(self):
        self.assertEqual(
            autoreload.get_child_arguments(),
            [sys.executable, "-m", "utils_tests.test_module", "runserver"],
        )