def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_blank_and_null_values(**kwargs),
        ]