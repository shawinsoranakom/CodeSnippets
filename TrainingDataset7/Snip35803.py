def test_inserting_reverse_lazy_into_string(self):
        self.assertEqual(
            "Some URL: %s" % reverse_lazy("some-login-page"), "Some URL: /login/"
        )