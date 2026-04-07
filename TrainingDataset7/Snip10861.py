def as_sql(self, compiler, connection):
        connection.ops.check_expression_support(self)
        val = self.value
        output_field = self._output_field_or_none
        if output_field is not None:
            if self.for_save:
                val = output_field.get_db_prep_save(val, connection=connection)
            else:
                val = output_field.get_db_prep_value(val, connection=connection)
            try:
                get_placeholder_sql = output_field.get_placeholder_sql
            except AttributeError:
                pass
            else:
                return get_placeholder_sql(val, compiler, connection)
        if val is None:
            # oracledb does not always convert None to the appropriate
            # NULL type (like in case expressions using numbers), so we
            # use a literal SQL NULL
            return "NULL", ()
        return "%s", (val,)