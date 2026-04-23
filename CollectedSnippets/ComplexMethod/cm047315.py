def unlink(self):
        self.check_access('unlink')
        ids_set = set(self.ids)
        for data in self.sorted(key='id', reverse=True):
            name = data.name
            if data.model.model in self.env:
                table = self.env[data.model.model]._table
            else:
                table = data.model.model.replace('.', '_')

            # double-check we are really going to delete all the owners of this schema element
            external_ids = {
                id_ for [id_] in self.env.execute_query(SQL(
                    """SELECT id from ir_model_constraint where name=%s""", name
                ))
            }
            if external_ids - ids_set:
                # as installed modules have defined this element we must not delete it!
                continue

            typ = data.type
            if typ in ('f', 'u'):
                # test if FK exists on this table
                # Since type='u' means any "other" constraint, to avoid issues we limit to
                # 'c' -> check, 'u' -> unique, 'x' -> exclude constraints, effective leaving
                # out 'p' -> primary key and 'f' -> foreign key, constraints.
                # For 'f', it could be on a related m2m table, in which case we ignore it.
                # See: https://www.postgresql.org/docs/9.5/catalog-pg-constraint.html
                hname = sql.make_identifier(name)
                if self.env.execute_query(SQL(
                    """SELECT
                    FROM pg_constraint cs
                    JOIN pg_class cl
                    ON (cs.conrelid = cl.oid)
                    WHERE cs.contype IN %s AND cs.conname = %s AND cl.relname = %s
                    AND cl.relnamespace = current_schema::regnamespace
                    """, ('c', 'u', 'x') if typ == 'u' else (typ,), hname, table
                )):
                    self.env.execute_query(SQL(
                        'ALTER TABLE %s DROP CONSTRAINT %s',
                        SQL.identifier(table),
                        SQL.identifier(hname),
                    ))
                    _logger.info('Dropped CONSTRAINT %s@%s', name, data.model.model)

            if typ == 'i':
                hname = sql.make_identifier(name)
                # drop index if it exists
                self.env.execute_query(SQL("DROP INDEX IF EXISTS %s", SQL.identifier(hname)))
                _logger.info('Dropped INDEX %s@%s', name, data.model.model)

        return super().unlink()