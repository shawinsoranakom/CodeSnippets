def _create(self, data_list: list[ValuesType]) -> Self:
        """ Create records from the stored field values in ``data_list``. """
        assert data_list
        cr = self.env.cr

        # insert rows in batches of maximum INSERT_BATCH_SIZE
        ids: list[int] = []                     # ids of created records
        other_fields: OrderedSet[Field] = OrderedSet()  # non-column fields

        for data_sublist in split_every(INSERT_BATCH_SIZE, data_list):
            stored_list = [data['stored'] for data in data_sublist]
            fnames = sorted({name for stored in stored_list for name in stored})

            columns: list[str] = []
            rows: list[list[typing.Any]] = [[] for _ in stored_list]
            for fname in fnames:
                field = self._fields[fname]
                if field.column_type:
                    columns.append(fname)
                    for stored, row in zip(stored_list, rows):
                        if fname in stored:
                            row.append(field.convert_to_column_insert(stored[fname], self, stored))
                        else:
                            row.append(SQL_DEFAULT)
                else:
                    other_fields.add(field)

                if field.type == 'properties':
                    # force calling fields.create for properties field because
                    # we might want to update the parent definition
                    other_fields.add(field)

            if not columns:
                # manage the case where we create empty records
                columns = ['id']
                for row in rows:
                    row.append(SQL_DEFAULT)

            cr.execute(SQL(
                'INSERT INTO %s (%s) VALUES %s RETURNING "id"',
                SQL.identifier(self._table),
                SQL(', ').join(map(SQL.identifier, columns)),
                SQL(', ').join(tuple(row) for row in rows),
            ))
            ids.extend(id_ for id_, in cr.fetchall())

        # put the new records in cache, and update inverse fields, for many2one
        # (using bin_size=False to put binary values in the right place)
        records = self.browse(ids)
        inverses_update = defaultdict(list)     # {(field, value): ids}
        common_set_vals = set(LOG_ACCESS_COLUMNS + ['id', 'parent_path'])
        for data, record in zip(data_list, records.with_context(bin_size=False)):
            data['record'] = record
            # DLE P104: test_inherit.py, test_50_search_one2many
            vals = dict({k: v for d in data['inherited'].values() for k, v in d.items()}, **data['stored'])
            set_vals = common_set_vals.union(vals)

            # put None in cache for all fields that are not part of the INSERT
            for field in self._fields.values():
                if not field.store:
                    continue
                if field.type in ('one2many', 'many2many'):
                    field._update_cache(record, ())
                elif field.name not in set_vals:
                    field._update_cache(record, None)

            for fname, value in vals.items():
                field = self._fields[fname]
                if field.type not in ('one2many', 'many2many', 'html'):
                    cache_value = field.convert_to_cache(value, record)
                    field._update_cache(record, cache_value)
                    if field.type in ('many2one', 'many2one_reference') and self.pool.field_inverses[field]:
                        inverses_update[(field, cache_value)].append(record.id)

        for (field, value), record_ids in inverses_update.items():
            field._update_inverses(self.browse(record_ids), value)

        # update parent_path
        records._parent_store_create()

        # protect fields being written against recomputation
        protected = [(data['protected'], data['record']) for data in data_list]
        with self.env.protecting(protected):
            # mark computed fields as todo
            records.modified(self._fields, create=True)

            if other_fields:
                # discard default values from context for other fields
                others = records.with_context(clean_context(self.env.context))
                for field in sorted(other_fields, key=attrgetter('_sequence')):
                    field.create([
                        (other, data['stored'][field.name])
                        for other, data in zip(others, data_list)
                        if field.name in data['stored']
                    ])

                # mark fields to recompute
                records.modified([field.name for field in other_fields], create=True)

        # check Python constraints for stored fields
        records._validate_fields(name for data in data_list for name in data['stored'])
        records.check_access('create')
        return records