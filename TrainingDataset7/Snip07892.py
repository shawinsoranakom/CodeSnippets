def __call__(self, value):
        keys = set(value)
        missing_keys = self.keys - keys
        if missing_keys:
            raise ValidationError(
                self.messages["missing_keys"],
                code="missing_keys",
                params={"keys": ", ".join(missing_keys)},
            )
        if self.strict:
            extra_keys = keys - self.keys
            if extra_keys:
                raise ValidationError(
                    self.messages["extra_keys"],
                    code="extra_keys",
                    params={"keys": ", ".join(extra_keys)},
                )