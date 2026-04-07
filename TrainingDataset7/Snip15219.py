def test_middleware_subclasses(self):
        self.assertEqual(admin.checks.check_dependencies(), [])