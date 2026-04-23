def diff(self, other: 'RecordSnapshot', force=False):
        """ Return the values in ``self`` that differ from ``other``. """

        # determine fields to return
        simple_fields_spec = {}
        x2many_fields_spec = {}
        for field_name, field_spec in self.fields_spec.items():
            if field_name == 'id':
                continue
            if not force and other.get(field_name) == self[field_name]:
                continue
            field = self.record._fields[field_name]
            if field.type in ('one2many', 'many2many'):
                x2many_fields_spec[field_name] = field_spec
            else:
                simple_fields_spec[field_name] = field_spec

        # use web_read() for simple fields
        [result] = self.record.web_read(simple_fields_spec)

        # discard the NewId from the dict
        result.pop('id')

        # for x2many fields: serialize value as commands
        for field_name, field_spec in x2many_fields_spec.items():
            commands = []

            self_value = self[field_name]
            other_value = {} if force else other.get(field_name) or {}
            if any(other_value):
                # other may be a snapshot for a real record, adapt its x2many ids
                other_value = {NewId(id_): snap for id_, snap in other_value.items()}

            # commands for removed lines
            field = self.record._fields[field_name]
            remove = Command.delete if field.type == 'one2many' else Command.unlink
            for id_ in other_value:
                if id_ not in self_value:
                    commands.append(remove(id_.origin or id_.ref or 0))

            # commands for modified or extra lines
            for id_, line_snapshot in self_value.items():
                if not force and id_ in other_value:
                    # existing line: check diff and send update
                    line_diff = line_snapshot.diff(other_value[id_])
                    if line_diff:
                        commands.append(Command.update(id_.origin or id_.ref or 0, line_diff))

                elif not id_.origin:
                    # new line: send diff from scratch
                    line_diff = line_snapshot.diff({})
                    commands.append((Command.CREATE, id_.origin or id_.ref or 0, line_diff))

                else:
                    # link line: send data to client
                    base_line = line_snapshot.record._origin
                    [base_data] = base_line.web_read(field_spec.get('fields') or {})
                    commands.append((Command.LINK, base_line.id, base_data))

                    # check diff and send update
                    base_snapshot = RecordSnapshot(base_line, field_spec.get('fields') or {})
                    line_diff = line_snapshot.diff(base_snapshot)
                    if line_diff:
                        commands.append(Command.update(id_.origin, line_diff))

            if commands:
                result[field_name] = commands

        return result