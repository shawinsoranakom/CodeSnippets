def _delete_unique_sql(
        self,
        model,
        name,
        condition=None,
        deferrable=None,
        include=None,
        opclasses=None,
        expressions=None,
        nulls_distinct=None,
    ):
        if not self._unique_supported(
            condition=condition,
            deferrable=deferrable,
            include=include,
            expressions=expressions,
            nulls_distinct=nulls_distinct,
        ):
            return None
        if condition or include or opclasses or expressions:
            sql = self.sql_delete_index
        else:
            sql = self.sql_delete_unique
        return self._delete_constraint_sql(sql, model, name)