def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_to_fields_exist(),
            *self._check_to_fields_composite_pk(),
            *self._check_unique_target(),
        ]