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