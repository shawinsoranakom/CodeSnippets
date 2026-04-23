def _table_sql(self) -> SQL:
        """ Return an :class:`SQL` object that represents SQL table identifier
        or table query.
        """
        table_query = self._table_query
        if table_query and isinstance(table_query, SQL):
            table_sql = SQL("(%s)", table_query)
        elif table_query:
            table_sql = SQL(f"({table_query})")
        else:
            table_sql = SQL.identifier(self._table)
        if not self._depends:
            return table_sql

        # add self._depends (and its transitive closure) as metadata to table_sql
        fields_to_flush: list[Field] = []
        models = [self]
        while models:
            current_model = models.pop()
            for model_name, field_names in current_model._depends.items():
                model = self.env[model_name]
                models.append(model)
                fields_to_flush.extend(model._fields[fname] for fname in field_names)

        return SQL().join([
            table_sql,
            *(SQL(to_flush=field) for field in fields_to_flush),
        ])