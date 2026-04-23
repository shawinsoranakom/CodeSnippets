def test_check_ignores_import_error_in_middleware(self):
        errors = checks.run_checks()
        self.assertEqual(errors, [])