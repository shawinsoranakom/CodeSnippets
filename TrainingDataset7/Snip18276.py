def test_validate_django_supplied_file(self):
        validator = CommonPasswordValidator()
        for password in validator.passwords:
            self.assertEqual(password, password.lower())