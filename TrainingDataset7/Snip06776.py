def select_format(self, compiler, sql, params):
        select = compiler.connection.ops.select_extent
        return select % sql if select else sql, params