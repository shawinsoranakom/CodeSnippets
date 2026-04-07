def test_validate_password(self):
        self.assertIsNone(validate_password("sufficiently-long"))
        msg_too_short = (
            "This password is too short. It must contain at least 12 characters."
        )

        with self.assertRaises(ValidationError) as cm:
            validate_password("django4242")
        self.assertEqual(cm.exception.messages, [msg_too_short])
        self.assertEqual(cm.exception.error_list[0].code, "password_too_short")

        with self.assertRaises(ValidationError) as cm:
            validate_password("password")
        self.assertEqual(
            cm.exception.messages, ["This password is too common.", msg_too_short]
        )
        self.assertEqual(cm.exception.error_list[0].code, "password_too_common")

        self.assertIsNone(validate_password("password", password_validators=[]))