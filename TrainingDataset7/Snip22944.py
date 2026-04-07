def clean(self):
                raise ValidationError(
                    "Non-field error.", code="secret", params={"a": 1, "b": 2}
                )