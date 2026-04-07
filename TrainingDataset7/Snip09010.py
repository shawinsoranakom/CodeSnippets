def handle_field(self, obj, field):
        self._current[field.name] = self._value_from_field(obj, field)