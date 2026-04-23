def test_run_as_module(self):
        self.assertEqual(
            autoreload.get_child_arguments(),
            [sys.executable, "-m", "django", "runserver"],
        )