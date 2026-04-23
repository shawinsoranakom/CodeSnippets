def supports_json_negative_indexing(self):
        return self.connection.oracle_version >= (21,)