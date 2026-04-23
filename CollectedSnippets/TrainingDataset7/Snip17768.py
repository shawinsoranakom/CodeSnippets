def test_custom_login_allowed_policy(self):
        # The user is inactive, but our custom form policy allows them to log
        # in.
        data = {
            "username": "inactive",
            "password": "password",
        }

        class AuthenticationFormWithInactiveUsersOkay(AuthenticationForm):
            def confirm_login_allowed(self, user):
                pass

        form = AuthenticationFormWithInactiveUsersOkay(None, data)
        self.assertTrue(form.is_valid())

        # Raise a ValidationError in the form to disallow some logins according
        # to custom logic.
        class PickyAuthenticationForm(AuthenticationForm):
            def confirm_login_allowed(self, user):
                if user.username == "inactive":
                    raise ValidationError("This user is disallowed.")
                raise ValidationError("Sorry, nobody's allowed in.")

        form = PickyAuthenticationForm(None, data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["This user is disallowed."])

        data = {
            "username": "testclient",
            "password": "password",
        }
        form = PickyAuthenticationForm(None, data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["Sorry, nobody's allowed in."])