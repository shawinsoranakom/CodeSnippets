def write_real(self, records_commands_list, create=False):
        """ Update real records. """
        # records_commands_list = [(records, commands), ...]
        if not records_commands_list:
            return

        model = records_commands_list[0][0].browse()
        comodel = model.env[self.comodel_name].with_context(**self.context)
        comodel = self._check_sudo_commands(comodel)

        if self.store:
            inverse = self.inverse_name
            to_create = []                      # line vals to create
            to_delete = []                      # line ids to delete
            to_link = defaultdict(OrderedSet)   # {record: line_ids}
            allow_full_delete = not create

            def unlink(lines):
                if getattr(comodel._fields[inverse], 'ondelete', False) == 'cascade':
                    to_delete.extend(lines._ids)
                else:
                    lines[inverse] = False

            def flush():
                if to_link:
                    before = {record: record[self.name] for record in to_link}
                if to_delete:
                    # unlink() will remove the lines from the cache
                    comodel.browse(to_delete).unlink()
                    to_delete.clear()
                if to_create:
                    # create() will add the new lines to the cache of records
                    comodel.create(to_create)
                    to_create.clear()
                if to_link:
                    for record, line_ids in to_link.items():
                        lines = comodel.browse(line_ids) - before[record]
                        # linking missing lines should fail
                        lines.mapped(inverse)
                        lines[inverse] = record
                    to_link.clear()

            for recs, commands in records_commands_list:
                for command in (commands or ()):
                    if command[0] == Command.CREATE:
                        for record in recs:
                            to_create.append(dict(command[2], **{inverse: record.id}))
                        allow_full_delete = False
                    elif command[0] == Command.UPDATE:
                        prefetch_ids = recs[self.name]._prefetch_ids
                        comodel.browse(command[1]).with_prefetch(prefetch_ids).write(command[2])
                    elif command[0] == Command.DELETE:
                        to_delete.append(command[1])
                    elif command[0] == Command.UNLINK:
                        unlink(comodel.browse(command[1]))
                    elif command[0] == Command.LINK:
                        to_link[recs[-1]].add(command[1])
                        allow_full_delete = False
                    elif command[0] in (Command.CLEAR, Command.SET):
                        line_ids = command[2] if command[0] == Command.SET else []
                        if not allow_full_delete:
                            # do not try to delete anything in creation mode if nothing has been created before
                            if line_ids:
                                # equivalent to Command.LINK
                                if line_ids.__class__ is int:
                                    line_ids = [line_ids]
                                to_link[recs[-1]].update(line_ids)
                                allow_full_delete = False
                            continue
                        flush()
                        # assign the given lines to the last record only
                        lines = comodel.browse(line_ids)
                        domain = self.get_comodel_domain(model) & Domain(inverse, 'in', recs.ids) & Domain('id', 'not in', lines.ids)
                        unlink(comodel.search(domain))
                        lines[inverse] = recs[-1]

            flush()

        else:
            ids = OrderedSet(rid for recs, cs in records_commands_list for rid in recs._ids)
            records = records_commands_list[0][0].browse(ids)

            def link(record, lines):
                ids = record[self.name]._ids
                self._update_cache(record, tuple(unique(ids + lines._ids)))

            def unlink(lines):
                for record in records:
                    self._update_cache(record, (record[self.name] - lines)._ids)

            for recs, commands in records_commands_list:
                for command in (commands or ()):
                    if command[0] == Command.CREATE:
                        for record in recs:
                            link(record, comodel.new(command[2], ref=command[1]))
                    elif command[0] == Command.UPDATE:
                        comodel.browse(command[1]).write(command[2])
                    elif command[0] == Command.DELETE:
                        unlink(comodel.browse(command[1]))
                    elif command[0] == Command.UNLINK:
                        unlink(comodel.browse(command[1]))
                    elif command[0] == Command.LINK:
                        link(recs[-1], comodel.browse(command[1]))
                    elif command[0] in (Command.CLEAR, Command.SET):
                        # assign the given lines to the last record only
                        self._update_cache(recs, ())
                        lines = comodel.browse(command[2] if command[0] == Command.SET else [])
                        self._update_cache(recs[-1], lines._ids)