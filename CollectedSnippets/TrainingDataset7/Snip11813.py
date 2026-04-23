def get_rhs_op(self, connection, rhs):
        # If the lookup value is a reference to another column or a transform,
        # then the SQL is something like:
        #     col LIKE othercol || '%%'
        if not self.is_simple_lookup:
            # In that case, prepare the LIKE clause using
            # DatabaseWrapper.pattern_ops.
            pattern = connection.pattern_ops[self.lookup_name].format(
                connection.pattern_esc
            )
            return pattern.format(rhs)
        else:
            # Otherwise, use the LIKE in DatabaseWrapper.operators.
            return super().get_rhs_op(connection, rhs)