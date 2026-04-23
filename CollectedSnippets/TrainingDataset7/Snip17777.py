def test_password_whitespace_not_stripped(self):
        data = {
            "username": "testuser",
            "password": " pass ",
        }
        form = AuthenticationForm(None, data)
        form.is_valid()  # Not necessary to have valid credentails for the test.
        self.assertEqual(form.cleaned_data["password"], data["password"])