def test_custom_error(self):
        class CustomMinimumLengthValidator(MinimumLengthValidator):
            def get_error_message(self):
                return "Your password must be %d characters long" % self.min_length

        expected_error = "Your password must be %d characters long"

        with self.assertRaisesMessage(ValidationError, expected_error % 8) as cm:
            CustomMinimumLengthValidator().validate("1234567")
        self.assertEqual(cm.exception.error_list[0].code, "password_too_short")

        with self.assertRaisesMessage(ValidationError, expected_error % 3) as cm:
            CustomMinimumLengthValidator(min_length=3).validate("12")