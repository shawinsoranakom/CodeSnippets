def clean(self):
        if self.name == "_invalid":
            raise ValidationError("invalid")