def _quote_name(self, name):
        return self.connection.ops.quote_name(name)