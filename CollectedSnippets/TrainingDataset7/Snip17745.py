def test_normalize_username(self):
        # The normalization happens in AbstractBaseUser.clean() and ModelForm
        # validation calls Model.clean().
        ohm_username = "testΩ"  # U+2126 OHM SIGN
        data = {
            "username": ohm_username,
            "password1": "pwd2",
            "password2": "pwd2",
        }
        form = self.form_class(data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertNotEqual(user.username, ohm_username)
        self.assertEqual(user.username, "testΩ")