def _read_group_groupby(self, alias: str, groupby_spec: str, query: Query) -> SQL:
        """ Return <SQL expression> corresponding to the given groupby element.
        The method also checks whether the fields used in the groupby are
        accessible for reading.
        """
        fname, seq_fnames, granularity = parse_read_group_spec(groupby_spec)
        if fname not in self._fields:
            raise ValueError(f"Invalid field {fname!r} on model {self._name!r}")

        field = self._fields[fname]

        if field.type == 'properties':
            sql_expr = self._read_group_groupby_properties(alias, field, seq_fnames, query)

        elif seq_fnames:
            if field.type != 'many2one':
                raise ValueError(f"Only many2one path is accepted for the {groupby_spec!r} groupby spec")

            comodel = self.env[field.comodel_name]
            coquery = comodel.with_context(active_test=False)._search([])
            if self.env.su or not coquery.where_clause:
                coalias = query.make_alias(alias, fname)
            else:
                coalias = query.make_alias(alias, f"{fname}__{self.env.uid}")
            condition = SQL(
                "%s = %s",
                self._field_to_sql(alias, fname, query),
                SQL.identifier(coalias, 'id'),
            )
            if coquery.where_clause:
                subselect_arg = SQL('%s.*', SQL.identifier(comodel._table))
                query.add_join('LEFT JOIN', coalias, coquery.subselect(subselect_arg), condition)
            else:
                query.add_join('LEFT JOIN', coalias, comodel._table, condition)
            return comodel._read_group_groupby(coalias, f"{seq_fnames}:{granularity}" if granularity else seq_fnames, query)

        elif granularity and field.type not in ('datetime', 'date', 'properties'):
            raise ValueError(f"Granularity set on a no-datetime field or property: {groupby_spec!r}")

        elif field.type == 'many2many':
            if field.related and not field.store:
                _model, field, alias = self._traverse_related_sql(alias, field, query)

            if not field.store:
                raise ValueError(f"Group by non-stored many2many field: {groupby_spec!r}")
            # special case for many2many fields: prepare a query on the comodel
            # and inject the query as an extra condition of the left join
            codomain = field.get_comodel_domain(self)
            comodel = self.env[field.comodel_name].with_context(**field.context)
            coquery = comodel._search(codomain, bypass_access=field.bypass_search_access)
            # LEFT JOIN {field.relation} AS rel_alias ON
            #     alias.id = rel_alias.{field.column1}
            #     AND rel_alias.{field.column2} IN ({coquery})
            rel_alias = query.make_alias(alias, field.name)
            condition = SQL(
                "%s = %s",
                SQL.identifier(alias, 'id'),
                SQL.identifier(rel_alias, field.column1),
            )
            if coquery.where_clause:
                condition = SQL(
                    "%s AND %s IN %s",
                    condition,
                    SQL.identifier(rel_alias, field.column2),
                    coquery.subselect(),
                )
            query.add_join("LEFT JOIN", rel_alias, field.relation, condition)
            return SQL.identifier(rel_alias, field.column2)

        else:
            sql_expr = self._field_to_sql(alias, fname, query)

        if field.type in ('datetime', 'date') or (field.type == 'properties' and granularity):
            if not granularity:
                raise ValueError(f"Granularity not set on a date(time) field: {groupby_spec!r}")
            if granularity not in READ_GROUP_ALL_TIME_GRANULARITY:
                raise ValueError(f"Granularity specification isn't correct: {granularity!r}")

            if granularity in READ_GROUP_NUMBER_GRANULARITY:
                sql_expr = field.property_to_sql(sql_expr, granularity, self, alias, query)
            elif field.type == 'datetime':
                # set the timezone only
                sql_expr = field.property_to_sql(sql_expr, 'tz', self, alias, query)

            if granularity == 'week':
                # first_week_day: 0=Monday, 1=Tuesday, ...
                first_week_day = int(get_lang(self.env).week_start) - 1
                days_offset = first_week_day and 7 - first_week_day
                interval = f"-{days_offset} DAY"
                sql_expr = SQL(
                    "(date_trunc('week', %s::timestamp - INTERVAL %s) + INTERVAL %s)",
                    sql_expr, interval, interval,
                )
            elif granularity in READ_GROUP_TIME_GRANULARITY:
                sql_expr = SQL("date_trunc(%s, %s::timestamp)", granularity, sql_expr)

            # If the granularity is a part number, the result is a number (double) so no conversion is needed
            if field.type == 'date' and granularity not in READ_GROUP_NUMBER_GRANULARITY:
                # If the granularity uses date_trunc, we need to convert the timestamp back to a date.
                sql_expr = SQL("%s::date", sql_expr)

        elif field.type == 'boolean':
            sql_expr = SQL("COALESCE(%s, FALSE)", sql_expr)

        return sql_expr