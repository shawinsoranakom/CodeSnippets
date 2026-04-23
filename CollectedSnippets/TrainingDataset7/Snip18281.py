def test_custom_error(self):
        class CustomNumericPasswordValidator(NumericPasswordValidator):
            def get_error_message(self):
                return "This password is all digits."

        expected_error = "This password is all digits."

        with self.assertRaisesMessage(ValidationError, expected_error):
            CustomNumericPasswordValidator().validate("42424242")