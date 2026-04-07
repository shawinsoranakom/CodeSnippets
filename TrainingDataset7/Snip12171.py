def as_sql(self):
        """
        Create the SQL for this query. Return the SQL string and list of
        parameters.
        """
        self.pre_sql_setup()
        if not self.query.values:
            return "", ()
        qn = self.quote_name
        values, update_params = [], []
        for field, model, val in self.query.values:
            if hasattr(val, "resolve_expression"):
                val = val.resolve_expression(
                    self.query, allow_joins=False, for_save=True
                )
                if val.contains_aggregate:
                    raise FieldError(
                        "Aggregate functions are not allowed in this query "
                        "(%s=%r)." % (field.name, val)
                    )
                if val.contains_over_clause:
                    raise FieldError(
                        "Window expressions are not allowed in this query "
                        "(%s=%r)." % (field.name, val)
                    )
                if isinstance(val, ColPairs):
                    raise FieldError(
                        "Composite primary keys expressions are not allowed "
                        "in this query (%s=F('pk'))." % field.name
                    )
            elif hasattr(val, "prepare_database_save"):
                if field.remote_field:
                    val = val.prepare_database_save(field)
                else:
                    raise TypeError(
                        "Tried to update field %s with a model instance, %r. "
                        "Use a value compatible with %s."
                        % (field, val, field.__class__.__name__)
                    )
            val = field.get_db_prep_save(val, connection=self.connection)

            quoted_name = qn(field.column)
            if (
                get_placeholder_sql := getattr(field, "get_placeholder_sql", None)
            ) is not None:
                sql, params = get_placeholder_sql(val, self, self.connection)
                values.append(f"{quoted_name} = {sql}")
                update_params.extend(params)
            elif hasattr(val, "as_sql"):
                sql, params = self.compile(val)
                values.append(f"{quoted_name} = {sql}")
                update_params.extend(params)
            else:
                values.append(f"{quoted_name} = %s")
                update_params.append(val)
        table = self.query.base_table
        result = [
            "UPDATE %s SET" % qn(table),
            ", ".join(values),
        ]
        try:
            where, params = self.compile(self.query.where)
        except FullResultSet:
            params = []
        else:
            result.append("WHERE %s" % where)
        if self.returning_fields:
            # Skip empty r_sql to allow subclasses to customize behavior for
            # 3rd party backends. Refs #19096.
            r_sql, self.returning_params = self.connection.ops.returning_columns(
                self.returning_fields
            )
            if r_sql:
                result.append(r_sql)
                params.extend(self.returning_params)
        return " ".join(result), tuple(update_params + params)