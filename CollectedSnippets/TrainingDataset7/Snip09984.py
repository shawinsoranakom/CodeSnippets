def get_field_type(self, data_type, description):
        field_type = super().get_field_type(data_type, description)
        if description.pk and field_type in {
            "BigIntegerField",
            "IntegerField",
            "SmallIntegerField",
        }:
            # No support for BigAutoField or SmallAutoField as SQLite treats
            # all integer primary keys as signed 64-bit integers.
            return "AutoField"
        if description.has_json_constraint:
            return "JSONField"
        return field_type