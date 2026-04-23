def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_mutually_exclusive_options(),
            *self._check_fix_default_value(),
        ]