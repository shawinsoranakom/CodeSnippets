def write_real(self, records_commands_list, create=False):
        # records_commands_list = [(records, commands), ...]
        if not records_commands_list:
            return

        model = records_commands_list[0][0].browse()
        comodel = model.env[self.comodel_name].with_context(**self.context)
        comodel = self._check_sudo_commands(comodel)
        cr = model.env.cr

        # determine old and new relation {x: ys}
        set = OrderedSet
        ids = set(rid for recs, cs in records_commands_list for rid in recs.ids)
        records = model.browse(ids)

        if self.store:
            # Using `record[self.name]` generates 2 SQL queries when the value
            # is not in cache: one that actually checks access rules for
            # records, and the other one fetching the actual data. We use
            # `self.read` instead to shortcut the first query.
            missing_ids = tuple(self._cache_missing_ids(records))
            if missing_ids:
                self.read(records.browse(missing_ids))

        # determine new relation {x: ys}
        old_relation = {record.id: set(record[self.name]._ids) for record in records}
        new_relation = {x: set(ys) for x, ys in old_relation.items()}

        # operations on new relation
        def relation_add(xs, y):
            for x in xs:
                new_relation[x].add(y)

        def relation_remove(xs, y):
            for x in xs:
                new_relation[x].discard(y)

        def relation_set(xs, ys):
            for x in xs:
                new_relation[x] = set(ys)

        def relation_delete(ys):
            # the pairs (x, y) have been cascade-deleted from relation
            for ys1 in old_relation.values():
                ys1 -= ys
            for ys1 in new_relation.values():
                ys1 -= ys

        for recs, commands in records_commands_list:
            to_create = []  # line vals to create
            to_delete = []  # line ids to delete
            for command in (commands or ()):
                if not isinstance(command, (list, tuple)) or not command:
                    continue
                if command[0] == Command.CREATE:
                    to_create.append((recs._ids, command[2]))
                elif command[0] == Command.UPDATE:
                    prefetch_ids = recs[self.name]._prefetch_ids
                    comodel.browse(command[1]).with_prefetch(prefetch_ids).write(command[2])
                elif command[0] == Command.DELETE:
                    to_delete.append(command[1])
                elif command[0] == Command.UNLINK:
                    relation_remove(recs._ids, command[1])
                elif command[0] == Command.LINK:
                    relation_add(recs._ids, command[1])
                elif command[0] in (Command.CLEAR, Command.SET):
                    # new lines must no longer be linked to records
                    to_create = [(set(ids) - set(recs._ids), vals) for (ids, vals) in to_create]
                    relation_set(recs._ids, command[2] if command[0] == Command.SET else ())

            if to_create:
                # create lines in batch, and link them
                lines = comodel.create([vals for ids, vals in to_create])
                for line, (ids, _vals) in zip(lines, to_create):
                    relation_add(ids, line.id)

            if to_delete:
                # delete lines in batch
                comodel.browse(to_delete).unlink()
                relation_delete(to_delete)

        # check comodel access of added records
        # we check the su flag of the environment of records, because su may be
        # disabled on the comodel
        if not model.env.su:
            try:
                comodel.browse(
                    co_id
                    for rec_id, new_co_ids in new_relation.items()
                    for co_id in new_co_ids - old_relation[rec_id]
                ).check_access('read')
            except AccessError as e:
                raise AccessError(model.env._("Failed to write field %s", self) + "\n" + str(e))

        # update the cache of self
        for record in records:
            self._update_cache(record, tuple(new_relation[record.id]))

        # determine the corecords for which the relation has changed
        modified_corecord_ids = set()

        # process pairs to add (beware of duplicates)
        pairs = [(x, y) for x, ys in new_relation.items() for y in ys - old_relation[x]]
        if pairs:
            if self.store:
                cr.execute(SQL(
                    "INSERT INTO %s (%s, %s) VALUES %s ON CONFLICT DO NOTHING",
                    SQL.identifier(self.relation),
                    SQL.identifier(self.column1),
                    SQL.identifier(self.column2),
                    SQL(", ").join(pairs),
                ))

            # update the cache of inverse fields
            y_to_xs = defaultdict(set)
            for x, y in pairs:
                y_to_xs[y].add(x)
                modified_corecord_ids.add(y)
            for invf in records.pool.field_inverses[self]:
                domain = invf.get_comodel_domain(comodel)
                valid_ids = set(records.filtered_domain(domain)._ids)
                if not valid_ids:
                    continue
                inv_cache = invf._get_cache(comodel.env)
                for y, xs in y_to_xs.items():
                    corecord = comodel.browse(y)
                    try:
                        ids0 = inv_cache[corecord.id]
                        ids1 = tuple(set(ids0) | (xs & valid_ids))
                        invf._update_cache(corecord, ids1)
                    except KeyError:
                        pass

        # process pairs to remove
        pairs = [(x, y) for x, ys in old_relation.items() for y in ys - new_relation[x]]
        if pairs:
            y_to_xs = defaultdict(set)
            for x, y in pairs:
                y_to_xs[y].add(x)
                modified_corecord_ids.add(y)

            if self.store:
                # express pairs as the union of cartesian products:
                #    pairs = [(1, 11), (1, 12), (1, 13), (2, 11), (2, 12), (2, 14)]
                # -> y_to_xs = {11: {1, 2}, 12: {1, 2}, 13: {1}, 14: {2}}
                # -> xs_to_ys = {{1, 2}: {11, 12}, {2}: {14}, {1}: {13}}
                xs_to_ys = defaultdict(set)
                for y, xs in y_to_xs.items():
                    xs_to_ys[frozenset(xs)].add(y)
                # delete the rows where (id1 IN xs AND id2 IN ys) OR ...
                cr.execute(SQL(
                    "DELETE FROM %s WHERE %s",
                    SQL.identifier(self.relation),
                    SQL(" OR ").join(
                        SQL("%s IN %s AND %s IN %s",
                            SQL.identifier(self.column1), tuple(xs),
                            SQL.identifier(self.column2), tuple(ys))
                        for xs, ys in xs_to_ys.items()
                    ),
                ))

            # update the cache of inverse fields
            for invf in records.pool.field_inverses[self]:
                inv_cache = invf._get_cache(comodel.env)
                for y, xs in y_to_xs.items():
                    corecord = comodel.browse(y)
                    try:
                        ids0 = inv_cache[corecord.id]
                        ids1 = tuple(id_ for id_ in ids0 if id_ not in xs)
                        invf._update_cache(corecord, ids1)
                    except KeyError:
                        pass

        if modified_corecord_ids:
            # trigger the recomputation of fields that depend on the inverse
            # fields of self on the modified corecords
            corecords = comodel.browse(modified_corecord_ids)
            corecords.modified([
                invf.name
                for invf in model.pool.field_inverses[self]
                if invf.model_name == self.comodel_name
            ])