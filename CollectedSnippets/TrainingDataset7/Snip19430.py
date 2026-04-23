def test_failure_view_invalid_signature(self):
        msg = (
            "The CSRF failure view "
            "'check_framework.test_security.failure_view_with_invalid_signature' "
            "does not take the correct number of arguments."
        )
        self.assertEqual(
            csrf.check_csrf_failure_view(None),
            [Error(msg, id="security.E101")],
        )