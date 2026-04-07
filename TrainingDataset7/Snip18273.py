def test_validate(self):
        expected_error = "This password is too common."
        self.assertIsNone(CommonPasswordValidator().validate("a-safe-password"))

        with self.assertRaisesMessage(ValidationError, expected_error):
            CommonPasswordValidator().validate("godzilla")