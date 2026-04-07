def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                self.get_error_message(),
                code="password_entirely_numeric",
            )