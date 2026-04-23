def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                self.get_error_message(),
                code="password_too_short",
                params={"min_length": self.min_length},
            )