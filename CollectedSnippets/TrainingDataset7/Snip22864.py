def test_changing_cleaned_data_in_clean(self):
        class UserForm(Form):
            username = CharField(max_length=10)
            password = CharField(widget=PasswordInput)

            def clean(self):
                data = self.cleaned_data

                # Return a different dict. We have not changed
                # self.cleaned_data.
                return {
                    "username": data["username"].lower(),
                    "password": "this_is_not_a_secret",
                }

        f = UserForm({"username": "SirRobin", "password": "blue"})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["username"], "sirrobin")