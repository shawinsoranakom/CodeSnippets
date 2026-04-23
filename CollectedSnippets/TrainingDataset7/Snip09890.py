def _get_sequence_name(self, table, column):
        with self.connection.cursor() as cursor:
            for sequence in self.connection.introspection.get_sequences(cursor, table):
                if sequence["column"] == column:
                    return sequence["name"]
        return None