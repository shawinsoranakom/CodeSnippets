def test_timeout(self):
        """The token is valid after n seconds, but no greater."""
        # Uses a mocked version of PasswordResetTokenGenerator so we can change
        # the value of 'now'.
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        now = datetime.now()
        p0 = MockedPasswordResetTokenGenerator(now)
        tk1 = p0.make_token(user)
        p1 = MockedPasswordResetTokenGenerator(
            now + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
        )
        self.assertIs(p1.check_token(user, tk1), True)
        p2 = MockedPasswordResetTokenGenerator(
            now + timedelta(seconds=(settings.PASSWORD_RESET_TIMEOUT + 1))
        )
        self.assertIs(p2.check_token(user, tk1), False)
        with self.settings(PASSWORD_RESET_TIMEOUT=60 * 60):
            p3 = MockedPasswordResetTokenGenerator(
                now + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)
            )
            self.assertIs(p3.check_token(user, tk1), True)
            p4 = MockedPasswordResetTokenGenerator(
                now + timedelta(seconds=(settings.PASSWORD_RESET_TIMEOUT + 1))
            )
            self.assertIs(p4.check_token(user, tk1), False)