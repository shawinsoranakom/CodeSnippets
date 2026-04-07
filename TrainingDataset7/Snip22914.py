def clean_special_safe_name(self):
                raise ValidationError(
                    mark_safe(
                        "'<b>%s</b>' is a safe string"
                        % self.cleaned_data["special_safe_name"]
                    )
                )