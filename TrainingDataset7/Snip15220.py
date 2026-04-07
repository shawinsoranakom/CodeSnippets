def test_admin_check_ignores_import_error_in_middleware(self):
        self.assertEqual(admin.checks.check_dependencies(), [])