def test_check_token_with_nonexistent_token_and_user(self):
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        p0 = PasswordResetTokenGenerator()
        tk1 = p0.make_token(user)
        self.assertIs(p0.check_token(None, tk1), False)
        self.assertIs(p0.check_token(user, None), False)