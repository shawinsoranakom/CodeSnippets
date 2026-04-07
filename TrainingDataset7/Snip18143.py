def test_normalize_username(self):
        self.assertEqual(IntegerUsernameUser().normalize_username(123), 123)