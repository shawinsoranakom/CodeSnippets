def clean(self):
                self.cleaned_data["name"] = self.cleaned_data["name"].upper()
                return self.cleaned_data