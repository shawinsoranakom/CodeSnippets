def check(self, env: Environment) -> None:
        """ Check the consistency of the cache for the given environment. """
        depends_context = env.registry.field_depends_context
        invalids = []

        def process(model: BaseModel, field: Field, field_cache):
            # ignore new records and records to flush
            dirty_ids = self.transaction.field_dirty.get(field, ())
            ids = [id_ for id_ in field_cache if id_ and id_ not in dirty_ids]
            if not ids:
                return

            # select the column for the given ids
            query = Query(env, model._table, model._table_sql)
            sql_id = SQL.identifier(model._table, 'id')
            sql_field = model._field_to_sql(model._table, field.name, query)
            if field.type == 'binary' and (
                model.env.context.get('bin_size') or model.env.context.get('bin_size_' + field.name)
            ):
                sql_field = SQL('pg_size_pretty(length(%s)::bigint)', sql_field)
            query.add_where(SQL("%s IN %s", sql_id, tuple(ids)))
            env.cr.execute(query.select(sql_id, sql_field))

            # compare returned values with corresponding values in cache
            for id_, value in env.cr.fetchall():
                cached = field_cache[id_]
                if value == cached or (not value and not cached):
                    continue
                invalids.append((model.browse((id_,)), field, {'cached': cached, 'fetched': value}))

        for field, field_cache in self.transaction.field_data.items():
            # check column fields only
            if not field.store or not field.column_type or field.translate or field.company_dependent:
                continue

            model = env[field.model_name]
            if field in depends_context:
                for context_keys, inner_cache in field_cache.items():
                    context = dict[str, typing.Any](zip(depends_context[field], context_keys))
                    if 'company' in context:
                        # the cache key 'company' actually comes from context
                        # key 'allowed_company_ids' (see property env.company
                        # and method env.cache_key())
                        context['allowed_company_ids'] = [context.pop('company')]
                    process(model.with_context(context), field, inner_cache)
            else:
                process(model, field, field_cache)

        if invalids:
            _logger.warning("Invalid cache: %s", pformat(invalids))