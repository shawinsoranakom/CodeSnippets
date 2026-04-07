def check(self, **kwargs):
        return [
            *self._check_field_name(),
            *self._check_choices(),
            *self._check_db_default(**kwargs),
            *self._check_db_index(),
            *self._check_db_comment(**kwargs),
            *self._check_null_allowed_for_primary_keys(),
            *self._check_backend_specific_checks(**kwargs),
            *self._check_validators(),
            *self._check_deprecation_details(),
        ]