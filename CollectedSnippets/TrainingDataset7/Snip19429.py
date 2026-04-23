def test_failure_view_import_error(self):
        self.assertEqual(
            csrf.check_csrf_failure_view(None),
            [
                Error(
                    "The CSRF failure view '' could not be imported.",
                    id="security.E102",
                )
            ],
        )