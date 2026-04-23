def clean(self):
                raise ValidationError(
                    "<p>Non-field error.</p>",
                    code="secret",
                    params={"a": 1, "b": 2},
                )