def test_correct_order_with_login_required_middleware(self):
        errors = checks.run_checks()
        self.assertEqual(errors, [])