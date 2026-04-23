def _fetch_query(self, query: Query, fields: Sequence[Field]) -> Self:
        """ Fetch the given fields (iterable of :class:`Field` instances) from
        the given query, put them in cache, and return the fetched records.

        This method may be overridden to change what fields to actually fetch,
        or to change the values that are put in cache.
        """

        # determine columns fields and those with their own read() method
        column_fields: OrderedSet[Field] = OrderedSet()
        other_fields: OrderedSet[Field] = OrderedSet()
        for field in fields:
            if field.name == 'id':
                continue
            assert field.store
            (column_fields if field.column_type else other_fields).add(field)

        context = self.env.context

        if column_fields:
            # the query may involve several tables: we need fully-qualified names
            sql_terms = [SQL.identifier(self._table, 'id')]
            for field in column_fields:
                if field.type == 'binary' and (
                        context.get('bin_size') or context.get('bin_size_' + field.name)):
                    # PG 9.2 introduces conflicting pg_size_pretty(numeric) -> need ::cast
                    sql = self._field_to_sql(self._table, field.name, query)
                    sql = SQL("pg_size_pretty(length(%s)::bigint)", sql)
                else:
                    sql = self._field_to_sql(self._table, field.name, query)
                    # flushing is necessary to retrieve the en_US value of fields without a translation
                    # otherwise, re-create the SQL without flushing
                    if not field.translate:
                        to_flush = (f for f in sql.to_flush if f != field)
                        sql = SQL(sql.code, *sql.params, to_flush=to_flush)
                sql_terms.append(sql)

            # select the given columns from the rows in the query
            rows = self.env.execute_query(query.select(*sql_terms))

            if not rows:
                return self.browse()

            # rows = [(id1, a1, b1), (id2, a2, b2), ...]
            # column_values = [(id1, id2, ...), (a1, a2, ...), (b1, b2, ...)]
            column_values = zip(*rows)
            ids = next(column_values)
            fetched = self.browse(ids)

            # If we assume that the value of a pending update is in cache, we
            # can avoid flushing pending updates if the fetched values do not
            # overwrite values in cache.
            for field, values in zip(column_fields, column_values, strict=True):
                # store values in cache, but without overwriting
                field._insert_cache(fetched, values)
        else:
            fetched = self.browse(query)

        # process non-column fields
        if fetched:
            for field in other_fields:
                field.read(fetched)

        return fetched