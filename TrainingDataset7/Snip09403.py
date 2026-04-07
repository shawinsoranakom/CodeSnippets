def _index_columns(self, table, columns, col_suffixes, opclasses):
        return Columns(table, columns, self.quote_name, col_suffixes=col_suffixes)