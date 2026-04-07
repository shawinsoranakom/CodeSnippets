def get_rhs_op(self, connection, rhs):
        return "BETWEEN %s AND %s" % (rhs[0], rhs[1])