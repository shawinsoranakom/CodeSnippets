def clean(self):
                self.cleaned_data["username"] = self.cleaned_data["username"].lower()