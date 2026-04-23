def supports_uuid4_function(self):
        return self.connection.oracle_version >= (23, 9)