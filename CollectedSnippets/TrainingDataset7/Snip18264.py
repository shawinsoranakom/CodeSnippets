def test_validate(self):
        expected_error = (
            "This password is too short. It must contain at least %d characters."
        )
        self.assertIsNone(MinimumLengthValidator().validate("12345678"))
        self.assertIsNone(MinimumLengthValidator(min_length=3).validate("123"))

        with self.assertRaises(ValidationError) as cm:
            MinimumLengthValidator().validate("1234567")
        self.assertEqual(cm.exception.messages, [expected_error % 8])
        error = cm.exception.error_list[0]
        self.assertEqual(error.code, "password_too_short")
        self.assertEqual(error.params, {"min_length": 8})

        with self.assertRaises(ValidationError) as cm:
            MinimumLengthValidator(min_length=3).validate("12")
        self.assertEqual(cm.exception.messages, [expected_error % 3])
        error = cm.exception.error_list[0]
        self.assertEqual(error.code, "password_too_short")
        self.assertEqual(error.params, {"min_length": 3})