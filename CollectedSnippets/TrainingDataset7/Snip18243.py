def test_make_token(self):
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        p0 = PasswordResetTokenGenerator()
        tk1 = p0.make_token(user)
        self.assertIs(p0.check_token(user, tk1), True)