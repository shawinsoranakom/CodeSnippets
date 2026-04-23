def test_invalid_username_no_normalize(self):
        field = UsernameField(max_length=254)
        # Usernames are not normalized if they are too long.
        self.assertEqual(field.to_python("½" * 255), "½" * 255)
        self.assertEqual(field.to_python("ﬀ" * 254), "ff" * 254)