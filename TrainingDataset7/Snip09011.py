def handle_fk_field(self, obj, field):
        if self.use_natural_foreign_keys and (
            natural_key_value := self._resolve_fk_natural_key(obj, field)
        ):
            value = natural_key_value
        else:
            value = self._value_from_field(obj, field)
        self._current[field.name] = value