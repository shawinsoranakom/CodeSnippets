def test_duplicate_normalized_unicode(self):
        """
        To prevent almost identical usernames, visually identical but differing
        by their unicode code points only, Unicode NFKC normalization should
        make appear them equal to Django.
        """
        omega_username = "iamtheΩ"  # U+03A9 GREEK CAPITAL LETTER OMEGA
        ohm_username = "iamtheΩ"  # U+2126 OHM SIGN
        self.assertNotEqual(omega_username, ohm_username)
        User.objects.create_user(username=omega_username, password="pwd")
        data = {
            "username": ohm_username,
            "password1": "pwd2",
            "password2": "pwd2",
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["username"], ["A user with that username already exists."]
        )