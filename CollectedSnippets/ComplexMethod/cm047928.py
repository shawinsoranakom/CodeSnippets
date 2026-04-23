def get_fields_tree(self, model, depth=FIELDS_RECURSION_LIMIT):
        """ Recursively get fields for the provided model (through
        fields_get) and filter them according to importability

        The output format is a list of :class:`Field`:

        .. class:: Field

            .. attribute:: id: str

                A non-unique identifier for the field, used to compute
                the span of the ``required`` attribute: if multiple
                ``required`` fields have the same id, only one of them
                is necessary.

            .. attribute:: name: str

                The field's logical (Odoo) name within the scope of
                its parent.

            .. attribute:: string: str

                The field's human-readable name (``@string``)

            .. attribute:: required: bool

                Whether the field is marked as required in the
                model. Clients must provide non-empty import values
                for all required fields or the import will error out.

            .. attribute:: fields: list[Field]

                The current field's subfields. The database and
                external identifiers for m2o and m2m fields; a
                filtered and transformed fields_get for o2m fields (to
                a variable depth defined by ``depth``).

                Fields with no sub-fields will have an empty list of
                sub-fields.

            .. attribute:: model_name: str

                Used in the Odoo Field Tooltip on the import view
                and to get the model of the field of the related field(s).
                Name of the current field's model.

            .. attribute:: comodel_name: str

                Used in the Odoo Field Tooltip on the import view
                and to get the model of the field of the related field(s).
                Name of the current field's comodel, i.e. if the field is a relation field.

        Structure example for 'crm.team' model for returned importable_fields::

            [
                {'name': 'message_ids', 'string': 'Messages', 'model_name': 'crm.team', 'comodel_name': 'mail.message', 'fields': [
                    {'name': 'moderation_status', 'string': 'Moderation Status', 'model_name': 'mail.message', 'fields': []},
                    {'name': 'body', 'string': 'Contents', 'model_name': 'mail.message', 'fields' : []}
                ]},
                {{'name': 'name', 'string': 'Sales Team', 'model_name': 'crm.team', 'fields' : []}
            ]

        :param str model: name of the model to get fields form
        :param int depth: depth of recursion into o2m fields
        """
        Model = self.env[model]
        importable_fields = [{
            'id': 'id',
            'name': 'id',
            'string': _("External ID"),
            'required': False,
            'fields': [],
            'type': 'id',
            'model_name': model,
        }]
        if not depth:
            return importable_fields

        model_fields = Model.fields_get(attributes=[
            'string', 'required', 'type', 'readonly', 'relation',
            'definition_record', 'definition_record_field',
        ])
        blacklist = models.MAGIC_COLUMNS

        for name, field in dict(model_fields).items():
            if field['type'] not in 'properties':
                continue
            definition_record = field['definition_record']
            definition_record_field = field['definition_record_field']

            target_model = Model.env[Model._fields[definition_record].comodel_name]

            # ignore if you cannot access to the target model or the field definition
            if not target_model.has_access('read'):
                continue
            if not target_model._has_field_access(target_model._fields[definition_record_field], 'read'):
                continue

            # Do not take into account the definition of archived parents,
            # we do not import archived records most of the time.
            definition_records = target_model.search_fetch(
                [(definition_record_field, '!=', False)],
                [definition_record_field, 'display_name'],
                order='id',  # Avoid complex order
            )

            for record in definition_records:
                for definition in record[definition_record_field]:
                    definition_type = definition['type']
                    if (
                        definition_type == 'separator' or
                        (
                            definition_type in ('many2one', 'many2many')
                            and definition.get('comodel') not in Model.env
                        )
                    ):
                        continue
                    id_field = f"{name}.{definition['name']}"
                    model_fields[id_field] = {
                        'type': definition_type,
                        'string': _(
                            "%(property_string)s (%(parent_name)s)",
                            property_string=definition['string'], parent_name=record.display_name,
                        ),
                    }
                    if definition_type in ('many2one', 'many2many'):
                        model_fields[id_field]['relation'] = definition['comodel']

        for name, field in model_fields.items():
            if name in blacklist:
                continue
            if field.get('readonly'):
                continue
            field_value = {
                'id': name,
                'name': name,
                'string': field['string'],
                # Y U NO ALWAYS HAS REQUIRED
                'required': bool(field.get('required')),
                'fields': [],
                'type': field['type'],
                'model_name': model,
            }

            if field['type'] in ('many2many', 'many2one'):
                field_value['fields'] = [
                    dict(field_value, model_name=field['relation'], name='id', string=_("External ID"), type='id'),
                    dict(field_value, model_name=field['relation'], name='.id', string=_("Database ID"), type='id'),
                ]
                field_value['comodel_name'] = field['relation']
            elif field['type'] == 'one2many':
                field_value['fields'] = self.get_fields_tree(field['relation'], depth=depth-1)
                if self.env.user.has_group('base.group_no_one'):
                    field_value['fields'].append(
                        dict(field_value, model_name=field['relation'], fields=[], name='.id', string=_("Database ID"), type='id')
                    )
                field_value['comodel_name'] = field['relation']

            importable_fields.append(field_value)

        return importable_fields