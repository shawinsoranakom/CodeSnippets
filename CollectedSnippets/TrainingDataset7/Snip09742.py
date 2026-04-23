def sequence_reset_by_name_sql(self, style, sequences):
        sql = []
        for sequence_info in sequences:
            no_autofield_sequence_name = self._get_no_autofield_sequence_name(
                sequence_info["table"]
            )
            table = self.quote_name(sequence_info["table"])
            column = self.quote_name(sequence_info["column"] or "id")
            query = self._sequence_reset_sql % {
                "no_autofield_sequence_name": no_autofield_sequence_name,
                "table": table,
                "column": column,
                "table_name": strip_quotes(table),
                "column_name": strip_quotes(column),
                "suffix": self.connection.features.bare_select_suffix,
            }
            sql.append(query)
        return sql