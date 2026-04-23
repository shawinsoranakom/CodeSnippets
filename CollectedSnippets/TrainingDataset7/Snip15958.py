def test_password_display_for_field_user_model(self):
        password_field = User._meta.get_field("password")
        for password in [
            "invalid",
            "md5$zjIiKM8EiyfXEGiexlQRw4$a59a82cf344546e7bc09cb5f2246370a",
            "!b7pk7RNudAXGTNLK6fW5YnBCLVE6UUmeoJJYQHaO",
        ]:
            with self.subTest(password=password):
                display_value = display_for_field(
                    password, password_field, self.empty_value
                )
                self.assertEqual(display_value, render_password_as_hash(password))