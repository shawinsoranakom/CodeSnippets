def get_field_type(self, data_type, description):
        field_type = super().get_field_type(data_type, description)
        if "auto_increment" in description.extra:
            if field_type == "IntegerField":
                return "AutoField"
            elif field_type == "BigIntegerField":
                return "BigAutoField"
            elif field_type == "SmallIntegerField":
                return "SmallAutoField"
        if description.is_unsigned:
            if field_type == "BigIntegerField":
                return "PositiveBigIntegerField"
            elif field_type == "IntegerField":
                return "PositiveIntegerField"
            elif field_type == "SmallIntegerField":
                return "PositiveSmallIntegerField"
        if description.data_type.upper() == "UUID":
            return "UUIDField"
        # JSON data type is an alias for LONGTEXT in MariaDB, use check
        # constraints clauses to introspect JSONField.
        if description.has_json_constraint:
            return "JSONField"
        return field_type