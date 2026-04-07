def test_secure_csp_invalid_values(self):
        """Check should fail when either CSP setting is not a dict."""
        for value in (
            False,
            True,
            0,
            42,
            "",
            "not-a-dict",
            set(),
            {"a", "b"},
            [],
            [1, 2, 3, 4],
        ):
            with self.subTest(value=value):
                csp_error = Error(
                    base.E026.msg % ("SECURE_CSP", value), id=base.E026.id
                )
                with self.settings(SECURE_CSP=value):
                    errors = base.check_csp_settings(None)
                    self.assertEqual(errors, [csp_error])
                csp_report_only_error = Error(
                    base.E026.msg % ("SECURE_CSP_REPORT_ONLY", value), id=base.E026.id
                )
                with self.settings(SECURE_CSP_REPORT_ONLY=value):
                    errors = base.check_csp_settings(None)
                    self.assertEqual(errors, [csp_report_only_error])
                with self.settings(SECURE_CSP=value, SECURE_CSP_REPORT_ONLY=value):
                    errors = base.check_csp_settings(None)
                    self.assertEqual(errors, [csp_error, csp_report_only_error])