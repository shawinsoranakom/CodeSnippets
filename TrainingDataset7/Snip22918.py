def clean(self):
                if (
                    self.cleaned_data.get("password1")
                    and self.cleaned_data.get("password2")
                    and self.cleaned_data["password1"] != self.cleaned_data["password2"]
                ):
                    raise ValidationError(
                        "Please make sure your passwords match.",
                        code="password_mismatch",
                    )