def check_indexes(self, cr: Cursor, model_names: Iterable[str]) -> None:
        """ Create or drop column indexes for the given models. """

        expected = [
            (sql.make_index_name(Model._table, field.name), Model._table, field)
            for model_name in model_names
            for Model in [self.models[model_name]]
            if Model._auto and not Model._abstract
            for field in Model._fields.values()
            if field.column_type and field.store
        ]
        if not expected:
            return

        # retrieve existing indexes with their corresponding table
        cr.execute("SELECT indexname, tablename FROM pg_indexes WHERE indexname IN %s"
                   "   AND schemaname = current_schema",
                   [tuple(row[0] for row in expected)])
        existing = dict(cr.fetchall())

        for indexname, tablename, field in expected:
            index = field.index
            assert index in ('btree', 'btree_not_null', 'trigram', True, False, None)
            if index and indexname not in existing:
                if index == 'trigram' and not self.has_trigram:
                    # Ignore if trigram index is not supported
                    continue
                if field.translate and index != 'trigram':
                    _schema.warning(f"Index attribute on {field!r} ignored, only trigram index is supported for translated fields")
                    continue

                column_expression = f'"{field.name}"'
                if index == 'trigram':
                    if field.translate:
                        column_expression = f'''(jsonb_path_query_array({column_expression}, '$.*')::text)'''
                    # add `unaccent` to the trigram index only because the
                    # trigram indexes are mainly used for (=)ilike search and
                    # unaccent is added only in these cases when searching
                    from odoo.modules.db import FunctionStatus  # noqa: PLC0415
                    if self.has_unaccent == FunctionStatus.INDEXABLE:
                        column_expression = self.unaccent(column_expression)
                    elif self.has_unaccent:
                        warnings.warn(
                            "PostgreSQL function 'unaccent' is present but not immutable, "
                            "therefore trigram indexes may not be effective.",
                            stacklevel=1,
                        )
                    expression = f'{column_expression} gin_trgm_ops'
                    method = 'gin'
                    where = ''
                elif index == 'btree_not_null' and field.company_dependent:
                    # company dependent condition will use extra
                    # `AND col IS NOT NULL` to use the index.
                    expression = f'({column_expression} IS NOT NULL)'
                    method = 'btree'
                    where = f'{column_expression} IS NOT NULL'
                else:  # index in ['btree', 'btree_not_null'， True]
                    expression = f'{column_expression}'
                    method = 'btree'
                    where = f'{column_expression} IS NOT NULL' if index == 'btree_not_null' else ''
                try:
                    with cr.savepoint(flush=False):
                        sql.create_index(cr, indexname, tablename, [expression], method, where)
                except psycopg2.OperationalError:
                    _schema.error("Unable to add index %r for %s", indexname, self)

            elif not index and tablename == existing.get(indexname):
                _schema.info("Keep unexpected index %s on table %s", indexname, tablename)