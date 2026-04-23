def test_error_missing_staticfiles(self):
        errors = check_storages(None)
        self.assertEqual(errors, [E005])