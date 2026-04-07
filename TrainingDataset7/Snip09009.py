def _value_from_field(self, obj, field):
        if isinstance(field, CompositePrimaryKey):
            return [self._value_from_field(obj, f) for f in field]
        value = field.value_from_object(obj)
        # Protected types (i.e., primitives like None, numbers, dates,
        # and Decimals) are passed through as is. All other values are
        # converted to string first.
        return value if is_protected_type(value) else field.value_to_string(obj)