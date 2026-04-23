def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        # Ignore precision for DecimalFields.
        db_type = self.lhs.output_field.cast_db_type(connection).split("(")[0]
        cast_type = self.type_mapping[db_type]
        return "%s::%s" % (rhs, cast_type), rhs_params