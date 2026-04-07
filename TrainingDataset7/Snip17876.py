def test_is_password_usable(self):
        passwords = ("lètmein_badencoded", "", None)
        for password in passwords:
            with self.subTest(password=password):
                self.assertIs(is_password_usable(password), True)