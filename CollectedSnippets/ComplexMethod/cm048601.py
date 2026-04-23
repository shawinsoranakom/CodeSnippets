def deref_values(values, model):
            """Replace xml_id references by database ids in all provided values.

            This allows to define all the data before the records even exist in the database.
            """
            fields = ((model._fields[k], k, v) for k, v in values.items() if k in model._fields)
            failed_fields = []
            for field, fname, value in fields:
                if not value:
                    values[fname] = False
                elif isinstance(value, str) and (
                    field.type == 'many2one'
                    or (field.type in ('integer', 'many2one_reference') and not value.isdigit())
                ):
                    try:
                        values[fname] = self.ref(value).id if value not in ('', 'False', 'None') else False
                    except ValueError:
                        if model._name == 'res.company':
                            # Try a fallback on the company when reloading/loading on a branch
                            values[fname] = self.env.company[fname] or self.env.company.root_id[fname] or False
                        else:
                            _logger.warning("Failed when trying to recover %s for field=%s", value, field)
                            failed_fields.append(fname)
                            values[fname] = False
                elif field.type in ('one2many', 'many2many') and isinstance(value[0], (list, tuple)):
                    for i, (command, _id, *last_part) in enumerate(value):
                        if last_part:
                            last_part = last_part[0]
                        # (0, 0, {'test': 'account.ref_name'}) -> Command.Create({'test': 13})
                        if command in (Command.CREATE, Command.UPDATE):
                            deref_values(last_part, self.env[field.comodel_name])
                        # (6, 0, ['account.ref_name']) -> Command.Set([13])
                        elif command == Command.SET:
                            for subvalue_idx, subvalue in enumerate(last_part):
                                if isinstance(subvalue, str):
                                    last_part[subvalue_idx] = self.ref(subvalue).id
                        elif command == Command.LINK and isinstance(_id, str):
                            value[i] = Command.link(self.ref(_id).id)
                elif field.type in ('one2many', 'many2many') and isinstance(value, str):
                    values[fname] = [Command.set([
                        self.ref(v).id
                        for v in value.split(',')
                        if v
                    ])]
            for fname in failed_fields:
                del values[fname]
            return values