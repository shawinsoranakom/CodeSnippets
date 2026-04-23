def test_error_empty_storages(self):
        errors = check_storages(None)
        self.assertEqual(errors, [E005])