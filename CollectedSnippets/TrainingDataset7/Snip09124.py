def __call__(self, value):
        # The maximum length of an email is 320 characters per RFC 3696
        # section 3.
        if not value or "@" not in value or len(value) > 320:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        user_part, domain_part = value.rsplit("@", 1)

        if not self.user_regex.match(user_part):
            raise ValidationError(self.message, code=self.code, params={"value": value})

        if domain_part not in self.domain_allowlist and not self.validate_domain_part(
            domain_part
        ):
            raise ValidationError(self.message, code=self.code, params={"value": value})