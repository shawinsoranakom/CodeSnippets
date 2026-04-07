def _must_transform_value(value, field):
        return value is not None and value.srid != field.srid