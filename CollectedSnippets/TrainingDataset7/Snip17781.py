def test_no_password(self):
        data = {"username": "username"}
        form = AuthenticationForm(None, data)
        self.assertIs(form.is_valid(), False)
        self.assertEqual(
            form["password"].errors, [Field.default_error_messages["required"]]
        )