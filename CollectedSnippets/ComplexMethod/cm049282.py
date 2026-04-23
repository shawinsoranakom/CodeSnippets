def _get_definitions(self, model_names):
        model_definitions = {}
        for model_name in model_names:
            model = self.env[model_name]
            # get fields, relational fields are kept only if the related model is in model_names
            fields_data_by_fname = {
                fname: field_data
                for fname, field_data in model.fields_get(
                    attributes={
                        'definition_record_field', 'definition_record', 'aggregator',
                        'name', 'readonly', 'related', 'relation', 'required', 'searchable',
                        'selection', 'sortable', 'store', 'string', 'tracking', 'type',
                    },
                ).items()
                if field_data.get('selectable', True) and (
                    not field_data.get('relation') or field_data['relation'] in model_names
                )
            }
            fields_data_by_fname = {
                fname: field_data
                for fname, field_data in fields_data_by_fname.items()
                if not field_data.get('related') or field_data['related'].split('.')[0] in fields_data_by_fname
            }
            for fname, field_data in fields_data_by_fname.items():
                if fname in model._fields:
                    inverse_fields = [
                        field for field in model.pool.field_inverses[model._fields[fname]]
                        if field.model_name in model_names
                        and model.env[field.model_name]._has_field_access(field, 'read')
                    ]
                    if inverse_fields:
                        field_data['inverse_fname_by_model_name'] = {field.model_name: field.name for field in inverse_fields}
                    if field_data['type'] == 'many2one_reference':
                        field_data['model_name_ref_fname'] = model._fields[fname].model_field
            model_definitions[model_name] = {
                'description': model._description,
                'fields': fields_data_by_fname,
                'inherit': [model_name for model_name in model._inherit_module if model_name in model_names],
                'order': model._order,
                'parent_name': model._parent_name,
                'rec_name': model._rec_name,
            }
        return model_definitions