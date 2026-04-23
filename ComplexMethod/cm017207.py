def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type in ["JSONField", "TextField"]:
            converters.append(self.convert_textfield_value)
        elif internal_type == "BinaryField":
            converters.append(self.convert_binaryfield_value)
        elif internal_type == "BooleanField":
            converters.append(self.convert_booleanfield_value)
        elif internal_type == "DateTimeField":
            if settings.USE_TZ:
                converters.append(self.convert_datetimefield_value)
        elif internal_type == "DateField":
            converters.append(self.convert_datefield_value)
        elif internal_type == "TimeField":
            converters.append(self.convert_timefield_value)
        elif internal_type == "UUIDField":
            converters.append(self.convert_uuidfield_value)
        # Oracle stores empty strings as null. If the field accepts the empty
        # string, undo this to adhere to the Django convention of using
        # the empty string instead of null.
        if expression.output_field.empty_strings_allowed:
            converters.append(
                self.convert_empty_bytes
                if internal_type == "BinaryField"
                else self.convert_empty_string
            )
        return converters