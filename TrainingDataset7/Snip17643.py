def test_middleware_subclasses(self):
        errors = checks.run_checks()
        self.assertEqual(errors, [])