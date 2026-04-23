def _using_sql(self, new_field, old_field):
        if new_field.generated:
            return ""
        using_sql = " USING %(column)s::%(type)s"
        new_internal_type = new_field.get_internal_type()
        old_internal_type = old_field.get_internal_type()
        if new_internal_type == "ArrayField" and new_internal_type == old_internal_type:
            # Compare base data types for array fields.
            if list(self._field_base_data_types(old_field)) != list(
                self._field_base_data_types(new_field)
            ):
                return using_sql
        elif self._field_data_type(old_field) != self._field_data_type(new_field):
            return using_sql
        return ""