def write_new(self, records_commands_list):
        if not records_commands_list:
            return

        model = records_commands_list[0][0].browse()
        comodel = model.env[self.comodel_name].with_context(**self.context)
        comodel = self._check_sudo_commands(comodel)

        ids = {record.id for records, _ in records_commands_list for record in records}
        records = model.browse(ids)

        def browse(ids):
            return comodel.browse([id_ and NewId(id_) for id_ in ids])

        # make sure self is in cache
        records[self.name]

        if self.store:
            inverse = self.inverse_name

            # make sure self's inverse is in cache
            inverse_field = comodel._fields[inverse]
            for record in records:
                inverse_field._update_cache(record[self.name], record.id)

            for recs, commands in records_commands_list:
                for command in commands:
                    if command[0] == Command.CREATE:
                        for record in recs:
                            line = comodel.new(command[2], ref=command[1])
                            line[inverse] = record
                    elif command[0] == Command.UPDATE:
                        browse([command[1]]).update(command[2])
                    elif command[0] == Command.DELETE:
                        browse([command[1]])[inverse] = False
                    elif command[0] == Command.UNLINK:
                        browse([command[1]])[inverse] = False
                    elif command[0] == Command.LINK:
                        browse([command[1]])[inverse] = recs[-1]
                    elif command[0] == Command.CLEAR:
                        self._update_cache(recs, ())
                    elif command[0] == Command.SET:
                        # assign the given lines to the last record only
                        self._update_cache(recs, ())
                        last, lines = recs[-1], browse(command[2])
                        self._update_cache(last, lines._ids)
                        inverse_field._update_cache(lines, last.id)

        else:
            def link(record, lines):
                ids = record[self.name]._ids
                self._update_cache(record, tuple(unique(ids + lines._ids)))

            def unlink(lines):
                for record in records:
                    self._update_cache(record, (record[self.name] - lines)._ids)

            for recs, commands in records_commands_list:
                for command in commands:
                    if command[0] == Command.CREATE:
                        for record in recs:
                            link(record, comodel.new(command[2], ref=command[1]))
                    elif command[0] == Command.UPDATE:
                        browse([command[1]]).update(command[2])
                    elif command[0] == Command.DELETE:
                        unlink(browse([command[1]]))
                    elif command[0] == Command.UNLINK:
                        unlink(browse([command[1]]))
                    elif command[0] == Command.LINK:
                        link(recs[-1], browse([command[1]]))
                    elif command[0] in (Command.CLEAR, Command.SET):
                        # assign the given lines to the last record only
                        self._update_cache(recs, ())
                        lines = browse(command[2] if command[0] == Command.SET else [])
                        self._update_cache(recs[-1], lines._ids)