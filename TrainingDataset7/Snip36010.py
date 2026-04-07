def test_warnoptions(self):
        self.assertEqual(
            autoreload.get_child_arguments(),
            [sys.executable, "-Werror", __file__, "runserver"],
        )