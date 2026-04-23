def get_rhs_op(self, connection, rhs):
        # Unlike BuiltinLookup, the GIS get_rhs_op() implementation should
        # return an object (SpatialOperator) with an as_sql() method to allow
        # for more complex computations (where the lhs part can be mixed in).
        return connection.ops.gis_operators[self.lookup_name]