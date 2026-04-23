def _create_index_sql(
        self,
        model,
        *,
        fields=None,
        name=None,
        suffix="",
        using="",
        db_tablespace=None,
        col_suffixes=(),
        sql=None,
        opclasses=(),
        condition=None,
        concurrently=False,
        include=None,
        expressions=None,
    ):
        sql = sql or (
            self.sql_create_index
            if not concurrently
            else self.sql_create_index_concurrently
        )
        return super()._create_index_sql(
            model,
            fields=fields,
            name=name,
            suffix=suffix,
            using=using,
            db_tablespace=db_tablespace,
            col_suffixes=col_suffixes,
            sql=sql,
            opclasses=opclasses,
            condition=condition,
            include=include,
            expressions=expressions,
        )