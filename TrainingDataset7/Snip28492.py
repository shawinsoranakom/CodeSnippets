def clean(self):
                if not self.cleaned_data["left"] == self.cleaned_data["right"]:
                    raise ValidationError("Left and right should be equal")
                return self.cleaned_data