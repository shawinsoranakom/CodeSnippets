def is_email_simple(value):
        """Return True if value looks like an email address."""
        try:
            EmailValidator(allowlist=[])(value)
        except ValidationError:
            return False
        return True