def test_token_with_different_email(self):
        """Updating the user email address invalidates the token."""
        tests = [
            (CustomEmailField, None),
            (CustomEmailField, "test4@example.com"),
            (User, "test4@example.com"),
        ]
        for model, email in tests:
            with self.subTest(model=model.__qualname__, email=email):
                user = model.objects.create_user(
                    "changeemailuser",
                    email=email,
                    password="testpw",
                )
                p0 = PasswordResetTokenGenerator()
                tk1 = p0.make_token(user)
                self.assertIs(p0.check_token(user, tk1), True)
                setattr(user, user.get_email_field_name(), "test4new@example.com")
                user.save()
                self.assertIs(p0.check_token(user, tk1), False)