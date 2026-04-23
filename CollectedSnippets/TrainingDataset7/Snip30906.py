def __call__(self, name):
            return connection.ops.quote_name(name)