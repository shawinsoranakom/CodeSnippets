def test_custom_email(self):
        user = CustomEmailField()
        self.assertEqual(user.get_email_field_name(), "email_address")