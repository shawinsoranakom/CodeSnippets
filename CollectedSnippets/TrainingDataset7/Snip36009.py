def test_run_as_non_django_module_non_package(self):
        self.assertEqual(
            autoreload.get_child_arguments(),
            [sys.executable, "-m", "utils_tests.test_module.main_module", "runserver"],
        )