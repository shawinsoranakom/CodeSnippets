def clean_special_name(self):
                raise ValidationError(
                    "Something's wrong with '%s'" % self.cleaned_data["special_name"]
                )