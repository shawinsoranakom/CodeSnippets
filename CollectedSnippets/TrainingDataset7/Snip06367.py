def validate(self, password, user=None):
        if password.lower().strip() in self.passwords:
            raise ValidationError(
                self.get_error_message(),
                code="password_too_common",
            )