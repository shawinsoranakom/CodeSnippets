def read(self, records):
        context = {'active_test': False}
        context.update(self.context)
        comodel = records.env[self.comodel_name].with_context(**context)

        # bypass the access during search if method is overwriten to avoid
        # possibly filtering all records of the comodel before joining
        filter_access = self.bypass_search_access and type(comodel)._search is not BaseModel._search

        # make the query for the lines
        domain = self.get_comodel_domain(records)
        try:
            query = comodel._search(domain, order=comodel._order, bypass_access=filter_access)
        except AccessError as e:
            raise AccessError(records.env._("Failed to read field %s", self) + '\n' + str(e)) from e

        # join with many2many relation table
        sql_id1 = SQL.identifier(self.relation, self.column1)
        sql_id2 = SQL.identifier(self.relation, self.column2)
        query.add_join('JOIN', self.relation, None, SQL(
            "%s = %s", sql_id2, SQL.identifier(comodel._table, 'id'),
        ))
        query.add_where(SQL("%s IN %s", sql_id1, tuple(records.ids)))

        # retrieve pairs (record, line) and group by record
        group = defaultdict(list)
        for id1, id2 in records.env.execute_query(query.select(sql_id1, sql_id2)):
            group[id1].append(id2)

        # filter using record rules
        if filter_access and group:
            corecord_ids = OrderedSet(id_ for ids in group.values() for id_ in ids)
            accessible_corecords = comodel.browse(corecord_ids)._filtered_access('read')
            if len(accessible_corecords) < len(corecord_ids):
                # some records are inaccessible, remove them from groups
                corecord_ids = set(accessible_corecords._ids)
                for id1, ids in group.items():
                    group[id1] = [id_ for id_ in ids if id_ in corecord_ids]

        # store result in cache
        values = [tuple(group[id_]) for id_ in records._ids]
        self._insert_cache(records, values)