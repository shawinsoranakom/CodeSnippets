def test_changing_cleaned_data_nothing_returned(self):
        class UserForm(Form):
            username = CharField(max_length=10)
            password = CharField(widget=PasswordInput)

            def clean(self):
                self.cleaned_data["username"] = self.cleaned_data["username"].lower()
                # don't return anything

        f = UserForm({"username": "SirRobin", "password": "blue"})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["username"], "sirrobin")