def _apply_onchange_(self, values, fields, onchange_values):
        assert isinstance(values, UpdateDict)
        for fname, value in onchange_values.items():
            field_info = fields[fname]
            if field_info['type'] in ('one2many', 'many2many'):
                subfields = {}
                if field_info['type'] == 'one2many':
                    subfields = field_info['edition_view']['fields']
                field_value = values[fname]
                for cmd in value:
                    match cmd[0]:
                        case Command.CREATE:
                            vals = UpdateDict(convert_read_to_form(dict.fromkeys(subfields, False), subfields))
                            self._apply_onchange_(vals, subfields, cmd[2])
                            field_value.create(vals)
                        case Command.UPDATE:
                            vals = field_value.get_vals(cmd[1])
                            self._apply_onchange_(vals, subfields, cmd[2])
                        case Command.DELETE | Command.UNLINK:
                            field_value.remove(cmd[1])
                        case Command.LINK:
                            field_value.add(cmd[1], convert_read_to_form(cmd[2], subfields))
                        case c:
                            raise ValueError(f"Unexpected onchange() o2m command {c!r}")
            else:
                values[fname] = value
            values._changed.add(fname)