def web_read(self, specification: dict[str, dict]) -> list[dict]:
        fields_to_read = list(specification) or ['id']

        if fields_to_read == ['id']:
            # if we request to read only the ids, we have them already so we can build the return dictionaries immediately
            # this also avoid a call to read on the co-model that might have different access rules
            values_list = [{'id': id_} for id_ in self._ids]
        else:
            values_list: list[dict] = self.read(fields_to_read, load=None)

        if not values_list:
            return values_list

        def cleanup(vals: dict) -> dict:
            """ Fixup vals['id'] of a new record. """
            if not vals['id']:
                vals['id'] = vals['id'].origin or False
            return vals

        for field_name, field_spec in specification.items():
            field = self._fields.get(field_name)
            if field is None:
                continue

            if field.type == 'many2one':
                if 'fields' not in field_spec:
                    for values in values_list:
                        if isinstance(values[field_name], NewId):
                            values[field_name] = values[field_name].origin
                    continue

                co_records = self[field_name]
                if 'context' in field_spec:
                    co_records = co_records.with_context(**field_spec['context'])

                extra_fields = dict(field_spec['fields'])
                extra_fields.pop('display_name', None)

                many2one_data = {
                    vals['id']: cleanup(vals)
                    for vals in co_records.web_read(extra_fields)
                }

                if 'display_name' in field_spec['fields']:
                    for rec in co_records.sudo():
                        many2one_data[rec.id]['display_name'] = rec.display_name

                for values in values_list:
                    if values[field_name] is False:
                        continue
                    vals = many2one_data[values[field_name]]
                    values[field_name] = vals['id'] and vals

            elif field.type in ('one2many', 'many2many'):
                if not field_spec:
                    continue

                co_records = self[field_name]

                field_spec_order = field_spec.get('order')
                field_spec_has_fields = 'fields' in field_spec
                has_co_records = any(co_records.ids)
                has_model_read_access = (
                    has_co_records
                    and co_records.env['ir.model.access'].check(
                        co_records._name, 'read', raise_exception=False,
                    )
                )

                # Filter out co-records the user cannot read (cache may keep
                # inaccessible ids after a sudo write/read).
                if field_spec_order and has_co_records:
                    if not has_model_read_access:
                        # If the comodel is not readable, keep the x2many empty.
                        co_records = co_records.browse()
                    else:
                        try:
                            co_records = co_records.with_context(active_test=False).search(
                                [('id', 'in', co_records.ids)], order=field_spec_order,
                            ).with_context(co_records.env.context)  # Reapply previous context
                        # Keep UserError if the model does not accept the search
                        # (e.g. account.code.mapping).
                        except (AccessError, UserError):
                            co_records = co_records.browse()

                elif field_spec_has_fields and has_model_read_access:
                    # Filter co-records only if the user can read the comodel.
                    # Some x2many fields have models that are not directly
                    # readable by the user (e.g. hr.employee from hr.appraisal for a
                    # base.group_user). In that case, keep the relation ids unchanged.
                    co_records = co_records.with_context(
                        active_test=False,
                    )._filtered_access('read').with_context(
                        co_records.env.context
                    )

                if has_co_records and (field_spec_order or field_spec_has_fields):
                    co_records_ids = set(co_records.ids)

                    for values in values_list:
                        # filter out inaccessible corecords in case of "cache pollution"
                        values[field_name] = [id_ for id_ in values[field_name] if id_ in co_records_ids]

                if field_spec_order:
                    order_key = {
                        co_record.id: index
                        for index, co_record in enumerate(co_records)
                    }
                    for values in values_list:
                        values[field_name] = sorted(values[field_name], key=order_key.__getitem__)

                if 'context' in field_spec:
                    co_records = co_records.with_context(**field_spec['context'])

                if field_spec_has_fields:
                    limit = field_spec.get('limit')
                    if limit is not None:
                        ids_to_read = OrderedSet(
                            id_
                            for values in values_list
                            for id_ in values[field_name][:limit]
                        )
                        co_records = co_records.browse(ids_to_read)

                    x2many_data = {
                        vals['id']: vals
                        for vals in co_records.web_read(field_spec['fields'])
                    }

                    for values in values_list:
                        values[field_name] = [x2many_data.get(id_) or {'id': id_} for id_ in values[field_name]]

            elif field.type in ('reference', 'many2one_reference'):
                if not field_spec:
                    continue

                values_by_id = {
                    vals['id']: vals
                    for vals in values_list
                }
                for record in self:
                    if not record[field_name]:
                        continue

                    record_values = values_by_id[record.id]

                    if field.type == 'reference':
                        co_record = record[field_name]
                    else:  # field.type == 'many2one_reference'
                        if not record[field.model_field]:
                            record_values[field_name] = False
                            continue
                        co_record = self.env[record[field.model_field]].browse(record[field_name])

                    if 'context' in field_spec:
                        co_record = co_record.with_context(**field_spec['context'])

                    if 'fields' in field_spec:
                        try:
                            reference_read = co_record.web_read(field_spec['fields'])
                        except AccessError:
                            reference_read = [{'id': co_record.id, 'display_name': self.env._("You don't have access to this record")}]
                        if any(fname != 'id' for fname in field_spec['fields']):
                            # we can infer that if we can read fields for the co-record, it exists
                            co_record_exists = bool(reference_read)
                        else:
                            co_record_exists = co_record.exists()
                    else:
                        # If there are no fields to read (field_spec.get('fields') --> None) and we web_read ids, it will
                        # not actually read the records so we do not know if they exist.
                        # This ensures the record actually exists
                        co_record_exists = co_record.exists()

                    if not co_record_exists:
                        record_values[field_name] = False
                        if field.type == 'many2one_reference':
                            record_values[field.model_field] = False
                        continue

                    if 'fields' in field_spec:
                        record_values[field_name] = reference_read[0]
                        if field.type == 'reference':
                            record_values[field_name]['id'] = {
                                'id': co_record.id,
                                'model': co_record._name
                            }

            elif field.type == "properties":
                if not field_spec or 'fields' not in field_spec:
                    continue

                for values in values_list:
                    old_values = values[field_name]
                    next_values = []
                    for property_name, spec in field_spec['fields'].items():
                        property_ = next((p for p in old_values if p.get('name') == property_name), None)
                        if not property_:
                            continue

                        if property_.get('type') == 'many2one' and property_.get('comodel') and property_.get('value'):
                            record = self.env[property_['comodel']].with_context(field_spec.get('context')).browse(property_['value'][0])
                            property_['value'] = record.web_read(spec['fields']) if 'fields' in spec else property_['value']

                        if property_.get('type') == 'many2many' and property_.get('comodel') and property_.get('value'):
                            records = self.env[property_['comodel']].with_context(field_spec.get('context')).browse([r[0] for r in property_['value']])
                            property_['value'] = records.web_read(spec['fields']) if 'fields' in spec else property_['value']

                        next_values.append(property_)

                    values[field_name] = next_values

        return values_list