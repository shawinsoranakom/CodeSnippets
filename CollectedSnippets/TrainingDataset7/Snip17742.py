def test_both_passwords(self):
        # One (or both) passwords weren't given
        data = {"username": "jsmith"}
        form = self.form_class(data)
        required_error = [str(Field.default_error_messages["required"])]
        self.assertFalse(form.is_valid())
        self.assertEqual(form["password1"].errors, required_error)
        self.assertEqual(form["password2"].errors, required_error)

        data["password2"] = "test123"
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form["password1"].errors, required_error)
        self.assertEqual(form["password2"].errors, [])