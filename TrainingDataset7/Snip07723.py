def as_postgresql(self, compiler, connection):
        sql, params = super().as_postgresql(compiler, connection)
        # Cast the rhs if needed.
        cast_sql = ""
        if (
            isinstance(self.rhs, models.Expression)
            and self.rhs._output_field_or_none
            and
            # Skip cast if rhs has a matching range type.
            not isinstance(
                self.rhs._output_field_or_none, self.lhs.output_field.__class__
            )
        ):
            cast_internal_type = self.lhs.output_field.base_field.get_internal_type()
            cast_sql = "::{}".format(connection.data_types.get(cast_internal_type))
        return "%s%s" % (sql, cast_sql), params