def clean(self):
                self.cleaned_data["mode"] = self.mocked_mode
                return self.cleaned_data