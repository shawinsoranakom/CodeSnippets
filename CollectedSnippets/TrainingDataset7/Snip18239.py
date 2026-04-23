def test_invalid_password(self):
        expected = (
            "<p><strong>Invalid password format or unknown hashing algorithm.</strong>"
            "</p>"
        )
        for value in ["pbkdf2_sh", "md5$password", "invalid", "testhash$password"]:
            with self.subTest(value=value):
                self.assertEqual(render_password_as_hash(value), expected)