def test_check_password_upgrade(self):
        """
        password_changed() shouldn't be called if User.check_password()
        triggers a hash iteration upgrade.
        """
        user = User.objects.create_user(username="user", password="foo")
        initial_password = user.password
        self.assertTrue(user.check_password("foo"))
        hasher = get_hasher("default")
        self.assertEqual("pbkdf2_sha256", hasher.algorithm)

        old_iterations = hasher.iterations
        try:
            # Upgrade the password iterations
            hasher.iterations = old_iterations + 1
            with mock.patch(
                "django.contrib.auth.password_validation.password_changed"
            ) as pw_changed:
                user.check_password("foo")
                self.assertEqual(pw_changed.call_count, 0)
            self.assertNotEqual(initial_password, user.password)
        finally:
            hasher.iterations = old_iterations