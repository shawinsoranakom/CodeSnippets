def get_rhs_op(self, connection, rhs):
        return connection.operators["exact"] % rhs