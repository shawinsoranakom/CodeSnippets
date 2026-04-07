def process_rhs(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        cast_type = self.lhs.output_field.cast_db_type(connection)
        return "%s::%s" % (rhs, cast_type), rhs_params