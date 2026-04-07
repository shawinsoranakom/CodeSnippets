def test_staticfiles_no_errors(self):
        errors = check_storages(None)
        self.assertEqual(errors, [])