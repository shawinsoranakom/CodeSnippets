def get_field_type(self, data_type, description):
        field_type = super().get_field_type(data_type, description)
        if description.is_autofield or (
            # Required for pre-Django 4.1 serial columns.
            description.default
            and "nextval" in description.default
        ):
            if field_type == "IntegerField":
                return "AutoField"
            elif field_type == "BigIntegerField":
                return "BigAutoField"
            elif field_type == "SmallIntegerField":
                return "SmallAutoField"
        return field_type