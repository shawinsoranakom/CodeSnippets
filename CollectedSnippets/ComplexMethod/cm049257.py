def _get_property_fields(self, fields, model, domain=()):
        """ Return property fields existing for the `domain` """
        property_fields = {}
        Model = request.env[model]
        for fname, field in fields.items():
            if field.get('type') != 'properties':
                continue

            definition_record = field['definition_record']
            definition_record_field = field['definition_record_field']

            # sudo(): user may lack access to property definition model
            target_model = Model.env[Model._fields[definition_record].comodel_name].sudo()
            domain_definition = [(definition_record_field, '!=', False)]
            # Depends of the records selected to avoid showing useless Properties
            if domain:
                self_subquery = Model.with_context(active_test=False)._search(domain)
                field_to_get = Model._field_to_sql(Model._table, definition_record, self_subquery)
                domain_definition.append(('id', 'in', self_subquery.subselect(field_to_get)))

            definition_records = target_model.search_fetch(
                domain_definition, [definition_record_field, 'display_name'],
                order='id',  # Avoid complex order
            )

            for record in definition_records:
                for definition in record[definition_record_field]:
                    # definition = {
                    #     'name': 'aa34746a6851ee4e',
                    #     'string': 'Partner',
                    #     'type': 'many2one',
                    #     'comodel': 'test_orm.partner',
                    #     'default': [1337, 'Bob'],
                    # }
                    if (
                        definition['type'] == 'separator' or
                        (
                            definition['type'] in ('many2one', 'many2many')
                            and definition.get('comodel') not in Model.env
                        )
                    ):
                        continue
                    id_field = f"{fname}.{definition['name']}"
                    property_fields[id_field] = {
                        'type': definition['type'],
                        'string': Model.env._(
                            "%(property_string)s (%(parent_name)s)",
                            property_string=definition['string'], parent_name=record.display_name,
                        ),
                        'default_export_compatible': field['default_export_compatible'],
                    }
                    if definition['type'] in ('many2one', 'many2many'):
                        property_fields[id_field]['relation'] = definition['comodel']

        return property_fields