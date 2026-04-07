async def test_acheck_password_upgrade(self):
        user = await User.objects.acreate_user(username="user", password="foo")
        initial_password = user.password
        self.assertIs(await user.acheck_password("foo"), True)
        hasher = get_hasher("default")
        self.assertEqual("pbkdf2_sha256", hasher.algorithm)

        old_iterations = hasher.iterations
        try:
            # Upgrade the password iterations.
            hasher.iterations = old_iterations + 1
            with mock.patch(
                "django.contrib.auth.password_validation.password_changed"
            ) as pw_changed:
                self.assertIs(await user.acheck_password("foo"), True)
                self.assertEqual(pw_changed.call_count, 0)
            self.assertNotEqual(initial_password, user.password)
        finally:
            hasher.iterations = old_iterations