def as_sqlite(self, compiler, connection, **extra_context):
        sql, params = self.as_sql(compiler, connection, **extra_context)
        if self.connector in {Combinable.MUL, Combinable.DIV}:
            try:
                lhs_type = self.lhs.output_field.get_internal_type()
                rhs_type = self.rhs.output_field.get_internal_type()
            except (AttributeError, FieldError):
                pass
            else:
                allowed_fields = {
                    "DecimalField",
                    "DurationField",
                    "FloatField",
                    "IntegerField",
                }
                if lhs_type not in allowed_fields or rhs_type not in allowed_fields:
                    raise DatabaseError(
                        f"Invalid arguments for operator {self.connector}."
                    )
        return sql, params