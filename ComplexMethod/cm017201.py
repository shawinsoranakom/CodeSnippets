def _unique_sql(
        self,
        model,
        fields,
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

        if (
            condition
            or include
            or opclasses
            or expressions
            or nulls_distinct is not None
        ):
            # Databases support conditional, covering, functional unique,
            # and nulls distinct constraints via a unique index.
            sql = self._create_unique_sql(
                model,
                fields,
                name=name,
                condition=condition,
                include=include,
                opclasses=opclasses,
                expressions=expressions,
                nulls_distinct=nulls_distinct,
            )
            if sql:
                self.deferred_sql.append(sql)
            return None
        constraint = self.sql_unique_constraint % {
            "columns": ", ".join([self.quote_name(field.column) for field in fields]),
            "deferrable": self._deferrable_constraint_sql(deferrable),
        }
        return self.sql_constraint % {
            "name": self.quote_name(name),
            "constraint": constraint,
        }