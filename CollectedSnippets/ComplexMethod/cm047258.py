def _str_to_one2many(self, model, field, records, savepoint):
        name_create_enabled_fields = self.env.context.get('name_create_enabled_fields') or {}
        prefix = field.name + '/'
        relative_name_create_enabled_fields = {
            k[len(prefix):]: v
            for k, v in name_create_enabled_fields.items()
            if k.startswith(prefix)
        }
        commands = []
        warnings = []

        if len(records) == 1 and exclude_ref_fields(records[0]) == {}:
            # only one row with only ref field, field=ref1,ref2,ref3 as in
            # m2o/m2m
            record = records[0]
            subfield, ws = self._referencing_subfield(record)
            warnings.extend(ws)
            # transform [{subfield:ref1,ref2,ref3}] into
            # [{subfield:ref1},{subfield:ref2},{subfield:ref3}]
            records = ({subfield:item} for item in record[subfield].split(','))

        def log(f, exception):
            if not isinstance(exception, Warning):
                current_field_name = self.env[field.comodel_name]._fields[f].string
                arg0 = exception.args[0].replace('%(field)s', '%(field)s/' + current_field_name)
                exception.args = (arg0, *exception.args[1:])
                raise exception
            warnings.append(exception)

        # Complete the field hierarchy path
        # E.g. For "parent/child/subchild", field hierarchy path for "subchild" is ['parent', 'child']
        parent_fields_hierarchy = self.env.context.get('parent_fields_hierarchy', []) + [field.name]

        convert = self.with_context(
            name_create_enabled_fields=relative_name_create_enabled_fields,
            parent_fields_hierarchy=parent_fields_hierarchy
        ).for_model(self.env[field.comodel_name], savepoint=savepoint)

        for record in records:
            id = None
            refs = only_ref_fields(record)
            writable = convert(exclude_ref_fields(record), log)
            if refs:
                subfield, w1 = self._referencing_subfield(refs)
                warnings.extend(w1)
                try:
                    id, w2 = self.db_id_for(model, field, subfield, record[subfield], savepoint)
                    warnings.extend(w2)
                except ValueError:
                    if subfield != 'id':
                        raise
                    writable['id'] = record['id']

            if id:
                commands.append(Command.link(id))
                commands.append(Command.update(id, writable))
            else:
                commands.append(Command.create(writable))

        return commands, warnings