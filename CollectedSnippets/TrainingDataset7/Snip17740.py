def test_invalid_data(self):
        data = {
            "username": "jsmith!",
            "password1": "test123",
            "password2": "test123",
        }
        form = self.form_class(data)
        self.assertFalse(form.is_valid())
        validator = next(
            v
            for v in User._meta.get_field("username").validators
            if v.code == "invalid"
        )
        self.assertEqual(form["username"].errors, [str(validator.message)])