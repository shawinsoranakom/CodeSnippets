def test_accessing_clean(self):
        class UserForm(Form):
            username = CharField(max_length=10)
            password = CharField(widget=PasswordInput)

            def clean(self):
                data = self.cleaned_data

                if not self.errors:
                    data["username"] = data["username"].lower()

                return data

        f = UserForm({"username": "SirRobin", "password": "blue"})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["username"], "sirrobin")