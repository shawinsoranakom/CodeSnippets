def test_invalid_middleware_skipped(self):
        errors = checks.run_checks()
        self.assertEqual(errors, [])