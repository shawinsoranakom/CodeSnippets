def get_sequences(self, cursor, table_name, table_fields=()):
        for field_info in self.get_table_description(cursor, table_name):
            if "auto_increment" in field_info.extra:
                # MySQL allows only one auto-increment column per table.
                return [{"table": table_name, "column": field_info.name}]
        return []