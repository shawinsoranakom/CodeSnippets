def _check_string_if_invalid_is_string(self):
        value = self.engine.string_if_invalid
        if not isinstance(value, str):
            return [
                Error(
                    "'string_if_invalid' in TEMPLATES OPTIONS must be a string but "
                    "got: %r (%s)." % (value, type(value)),
                    obj=self,
                    id="templates.E002",
                )
            ]
        return []