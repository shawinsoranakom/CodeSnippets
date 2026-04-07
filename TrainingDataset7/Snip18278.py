def test_custom_error(self):
        class CustomCommonPasswordValidator(CommonPasswordValidator):
            def get_error_message(self):
                return "This password has been used too much."

        expected_error = "This password has been used too much."

        with self.assertRaisesMessage(ValidationError, expected_error):
            CustomCommonPasswordValidator().validate("godzilla")