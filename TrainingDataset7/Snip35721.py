def test_invalid_kwargs(self):
        msg = "kwargs argument must be a dict, but got str."
        with self.assertRaisesMessage(TypeError, msg):
            path("hello/", empty_view, "name")
        with self.assertRaisesMessage(TypeError, msg):
            re_path("^hello/$", empty_view, "name")