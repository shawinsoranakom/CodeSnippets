def _update_foreign_keys_generic(self, model, src_records, dst_record):
        """ Update all foreign key from the src_records to dst_record for any model.
            :param model: model name as a string
            :param src_records: merge source recordset (does not include destination one)
            :param dst_record: record of destination
        """
        _logger.debug('_update_foreign_keys_generic for dst_record: %s for src_records: %s', dst_record.id, str(src_records.ids))

        relations = self._get_fk_on(self.env[model]._table)

        # this guarantees cache consistency
        self.env.invalidate_all()

        for table, column in relations:
            if 'base_partner_merge_' in table:  # ignore two tables
                continue

            # get list of columns of current table (except the current fk column)
            columns = [fld for fld in table_columns(self.env.cr, table) if fld != column]

            # do the update for the current table/column in SQL
            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }

            self.env.cr.execute('SELECT FROM "%(table)s" WHERE "%(column)s" IN %%s LIMIT 1' % query_dic,
                                (tuple(src_records.ids),))
            if self.env.cr.fetchone() is None:
                continue  # no record

            if len(columns) <= 1:
                # unique key treated
                query = """
                    UPDATE "%(table)s" as ___tu
                    SET "%(column)s" = %%s
                    WHERE
                        "%(column)s" = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                "%(column)s" = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )""" % query_dic
                for record in src_records:
                    self.env.cr.execute(query, (dst_record.id, record.id, dst_record.id))
            elif not self._has_check_or_unique_constraint(table, column):
                # if there is no CHECK or UNIQUE constraint, we do it without a savepoint
                query = 'UPDATE "%(table)s" SET "%(column)s" = %%s WHERE "%(column)s" IN %%s' % query_dic
                self.env.cr.execute(query, (dst_record.id, tuple(src_records.ids)))
            else:
                try:
                    with mute_logger('odoo.sql_db'), self.env.cr.savepoint():
                        query = 'UPDATE "%(table)s" SET "%(column)s" = %%s WHERE "%(column)s" IN %%s' % query_dic
                        self.env.cr.execute(query, (dst_record.id, tuple(src_records.ids)))
                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent partner_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s" IN %%s' % query_dic
                    self.env.cr.execute(query, (tuple(src_records.ids),))