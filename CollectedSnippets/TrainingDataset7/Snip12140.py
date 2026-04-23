def compile(self, node):
        vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
        if vendor_impl:
            sql, params = vendor_impl(self, self.connection)
        else:
            sql, params = node.as_sql(self, self.connection)
        return sql, params