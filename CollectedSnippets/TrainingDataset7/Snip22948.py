def clean(self):
                data = self.cleaned_data

                if not self.errors:
                    data["username"] = data["username"].lower()

                return data