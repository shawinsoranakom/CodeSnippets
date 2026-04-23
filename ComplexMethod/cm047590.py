def _order_field_to_sql(self, alias: str, field_name: str, direction: SQL,
                            nulls: SQL, query: Query) -> SQL:
        """ Return an :class:`SQL` object that represents the ordering by the
        given field.  The method also checks whether the field is accessible for
        reading.

        :param direction: one of ``SQL("ASC")``, ``SQL("DESC")``, ``SQL()``
        :param nulls: one of ``SQL("NULLS FIRST")``, ``SQL("NULLS LAST")``, ``SQL()``
        """
        # field_name is an expression
        fname, property_name = parse_field_expr(field_name)
        field = self._fields.get(fname)
        if not field:
            raise ValueError(f"Invalid field {fname!r} on model {self._name!r}")

        if field.type == 'many2one':
            seen = self.env.context.get('__m2o_order_seen', ())
            if field in seen:
                return SQL()
            self = self.with_context(__m2o_order_seen=frozenset((field, *seen)))

            # figure out the applicable order_by for the m2o
            # special case: ordering by "x_id.id" doesn't recurse on x_id's comodel
            comodel = self.env[field.comodel_name]
            if property_name == 'id':
                coorder = 'id'
                sql_field = self._field_to_sql(alias, fname, query)
            else:
                coorder = comodel._order
                sql_field = self._field_to_sql(alias, field_name, query)

            if coorder == 'id':
                query._order_groupby.append(sql_field)
                return SQL("%s %s %s", sql_field, direction, nulls)

            # instead of ordering by the field's raw value, use the comodel's
            # order on many2one values
            terms = []
            if nulls.code == 'NULLS FIRST':
                terms.append(SQL("%s IS NOT NULL", sql_field))
            elif nulls.code == 'NULLS LAST':
                terms.append(SQL("%s IS NULL", sql_field))

            # LEFT JOIN the comodel table, in order to include NULL values, too
            _comodel, coalias = field.join(self, alias, query)

            # delegate the order to the comodel
            reverse = direction.code == 'DESC'
            term = comodel._order_to_sql(coorder, query, alias=coalias, reverse=reverse)
            if term:
                terms.append(term)
            return SQL(", ").join(terms)

        sql_field = self._field_to_sql(alias, field_name, query)
        if field.type == 'boolean':
            sql_field = SQL("COALESCE(%s, FALSE)", sql_field)

        query._order_groupby.append(sql_field)

        return SQL("%s %s %s", sql_field, direction, nulls)