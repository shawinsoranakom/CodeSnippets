def _value_from_field(self, obj, field):
        # A nasty special case: base YAML doesn't support serialization of time
        # types (as opposed to dates or datetimes, which it does support).
        # Since we want to use the "safe" serializer for better
        # interoperability, we need to do something with those pesky times.
        # Converting 'em to strings isn't perfect, but it's better than a
        # "!!python/time" type which would halt deserialization under any other
        # language.
        value = super()._value_from_field(obj, field)
        if isinstance(value, datetime.time):
            value = str(value)
        return value