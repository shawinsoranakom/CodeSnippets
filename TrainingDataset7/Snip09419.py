def _unique_constraint_name(self, table, columns, quote=True):
        if quote:

            def create_unique_name(*args, **kwargs):
                return self.quote_name(self._create_index_name(*args, **kwargs))

        else:
            create_unique_name = self._create_index_name

        return IndexName(table, columns, "_uniq", create_unique_name)