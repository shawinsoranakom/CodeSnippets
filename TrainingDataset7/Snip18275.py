def test_validate_custom_list(self):
        path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "common-passwords-custom.txt"
        )
        validator = CommonPasswordValidator(password_list_path=path)
        expected_error = "This password is too common."
        self.assertIsNone(validator.validate("a-safe-password"))

        with self.assertRaises(ValidationError) as cm:
            validator.validate("from-my-custom-list")
        self.assertEqual(cm.exception.messages, [expected_error])
        self.assertEqual(cm.exception.error_list[0].code, "password_too_common")