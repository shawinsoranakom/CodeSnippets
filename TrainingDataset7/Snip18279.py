def test_validate(self):
        expected_error = "This password is entirely numeric."
        self.assertIsNone(NumericPasswordValidator().validate("a-safe-password"))

        with self.assertRaises(ValidationError) as cm:
            NumericPasswordValidator().validate("42424242")
        self.assertEqual(cm.exception.messages, [expected_error])
        self.assertEqual(cm.exception.error_list[0].code, "password_entirely_numeric")