def compile(self, node):
            return node.as_sql(self, connection)