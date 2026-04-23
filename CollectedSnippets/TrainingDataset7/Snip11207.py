def _check_str_default_value(self):
        if self.has_default() and isinstance(self.default, str):
            return [
                checks.Error(
                    "BinaryField's default cannot be a string. Use bytes "
                    "content instead.",
                    obj=self,
                    id="fields.E170",
                )
            ]
        return []