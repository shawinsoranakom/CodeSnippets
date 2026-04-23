def supports_tuple_lookups(self):
        # Support is known to be missing on 23.2 but available on 23.4.
        return self.connection.oracle_version >= (23, 4)