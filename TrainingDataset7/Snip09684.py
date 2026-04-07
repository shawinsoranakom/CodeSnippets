def supports_primitives_in_json_field(self):
        return self.connection.oracle_version >= (21,)