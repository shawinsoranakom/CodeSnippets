def _index_columns(self, table, columns, col_suffixes, opclasses):
        if opclasses:
            return IndexColumns(
                table,
                columns,
                self.quote_name,
                col_suffixes=col_suffixes,
                opclasses=opclasses,
            )
        return super()._index_columns(table, columns, col_suffixes, opclasses)