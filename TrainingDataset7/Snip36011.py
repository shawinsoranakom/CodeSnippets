def test_xoptions(self):
        self.assertEqual(
            autoreload.get_child_arguments(),
            [sys.executable, "-Xutf8", "-Xa=b", __file__, "runserver"],
        )