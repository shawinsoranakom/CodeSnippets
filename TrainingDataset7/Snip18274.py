def test_common_hexed_codes(self):
        expected_error = "This password is too common."
        common_hexed_passwords = ["asdfjkl:", "&#2336:"]
        for password in common_hexed_passwords:
            with self.subTest(password=password):
                with self.assertRaisesMessage(ValidationError, expected_error):
                    CommonPasswordValidator().validate(password)