def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_primary_key(),
        ]