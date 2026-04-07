def _rename_field_sql(self, table, old_field, new_field, new_type):
        new_type = self._set_field_new_type(old_field, new_type)
        return super()._rename_field_sql(table, old_field, new_field, new_type)