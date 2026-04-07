def clean(self):
                data = self.cleaned_data

                # Return a different dict. We have not changed
                # self.cleaned_data.
                return {
                    "username": data["username"].lower(),
                    "password": "this_is_not_a_secret",
                }