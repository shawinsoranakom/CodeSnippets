def process_rhs(self, compiler, connection):
        rhs = self.rhs
        if isinstance(rhs, int):
            field_internal_type = self.lhs.output_field.get_internal_type()
            min_value, max_value = connection.ops.integer_field_range(
                field_internal_type
            )
            if min_value is not None and rhs < min_value:
                raise self.underflow_exception
            if max_value is not None and rhs > max_value:
                raise self.overflow_exception
        return super().process_rhs(compiler, connection)