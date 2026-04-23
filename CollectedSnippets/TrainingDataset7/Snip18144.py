def test_clean_normalize_username(self):
        # The normalization happens in AbstractBaseUser.clean()
        ohm_username = "iamtheΩ"  # U+2126 OHM SIGN
        for model in ("auth.User", "auth_tests.CustomUser"):
            with self.subTest(model=model), self.settings(AUTH_USER_MODEL=model):
                User = get_user_model()
                user = User(**{User.USERNAME_FIELD: ohm_username, "password": "foo"})
                user.clean()
                username = user.get_username()
                self.assertNotEqual(username, ohm_username)
                self.assertEqual(
                    username, "iamtheΩ"
                )