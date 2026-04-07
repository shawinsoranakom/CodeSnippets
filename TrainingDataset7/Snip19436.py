def test_secure_csp_allowed_values(self):
        """Check should pass when both CSP settings are None or dicts."""
        allowed_values = (None, {}, {"key": "value"})
        combinations = itertools.product(allowed_values, repeat=2)
        for csp_value, csp_report_only_value in combinations:
            with (
                self.subTest(
                    csp_value=csp_value, csp_report_only_value=csp_report_only_value
                ),
                self.settings(
                    SECURE_CSP=csp_value, SECURE_CSP_REPORT_ONLY=csp_report_only_value
                ),
            ):
                errors = base.check_csp_settings(None)
                self.assertEqual(errors, [])