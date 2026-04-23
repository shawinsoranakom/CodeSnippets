def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_generic_foreign_key_existence(),
        ]