def supports_stored_generated_columns(self):
        return self.connection.oracle_version >= (23, 7)