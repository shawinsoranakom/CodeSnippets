def get_fields(self, model, domain, prefix='', parent_name='',
                   import_compat=True, parent_field_type=None,
                   parent_field=None, exclude=None):

        Model = request.env[model]
        fields = Model.fields_get(
            attributes=[
                'type', 'string', 'required', 'relation_field', 'default_export_compatible',
                'relation', 'definition_record', 'definition_record_field', 'exportable', 'readonly',
            ],
        )

        if import_compat:
            if parent_field_type in ['many2one', 'many2many']:
                rec_name = Model._rec_name_fallback()
                fields = {'id': fields['id'], rec_name: fields[rec_name]}
        else:
            fields['.id'] = {**fields['id']}

        fields['id']['string'] = request.env._('External ID')

        if not Model._is_an_ordinary_table():
            fields.pop("id", None)
        elif parent_field:
            parent_field['string'] = request.env._('External ID')
            fields['id'] = parent_field
            fields['id']['type'] = parent_field['field_type']

        exportable_fields = {}
        for field_name, field in fields.items():
            if import_compat and field_name != 'id':
                if exclude and field_name in exclude:
                    continue
                if field.get('readonly'):
                    continue
            if not field.get('exportable', True):
                continue
            exportable_fields[field_name] = field

        exportable_fields.update(self._get_property_fields(fields, model, domain=domain))

        fields_sequence = sorted(exportable_fields.items(), key=lambda field: field[1]['string'].lower())

        result = []
        for field_name, field in fields_sequence:
            ident = prefix + ('/' if prefix else '') + field_name
            val = ident
            if field_name == 'name' and import_compat and parent_field_type in ['many2one', 'many2many']:
                # Add name field when expand m2o and m2m fields in import-compatible mode
                val = prefix
            name = parent_name + (parent_name and '/' or '') + field['string']
            field_dict = {
                'id': ident,
                'string': name,
                'value': val,
                'children': False,
                'field_type': field.get('type'),
                'required': field.get('required'),
                'relation_field': field.get('relation_field'),
                'default_export': import_compat and field.get('default_export_compatible')
            }
            if len(ident.split('/')) < 3 and 'relation' in field:
                field_dict['value'] += '/id'
                field_dict['params'] = {
                    'model': field['relation'],
                    'prefix': ident,
                    'name': name,
                    'parent_field': field,
                }
                field_dict['children'] = True

            result.append(field_dict)

        return result