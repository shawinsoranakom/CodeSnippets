def _compute_string_to_hash(self):
        def _getattrstring(field_value, field_type, model_name=None):
            if field_type in ('many2many', 'one2many'):
                if field_value:
                    sorted_ids = sorted_relational_ids.get(model_name, [])
                    value_set = set(field_value)
                    field_value = [id for id in sorted_ids if id in value_set]
                else:
                    field_value = []
            return str(field_value)

        def collect_sorted_relational_ids(orders_data, lines_data, order_field_defs, line_field_defs):
            relational_ids = defaultdict(set)

            for data_list, field_names, field_defs in (
                (orders_data, fields_to_fetch, order_field_defs),
                (lines_data, LINE_FIELDS, line_field_defs),
            ):
                for record in data_list:
                    for field in field_names:
                        field_def = field_defs.get(field)
                        if field_def and field_def['type'] in ('many2many', 'one2many'):
                            ids = record.get(field) or []
                            relational_ids[field_def['comodel']].update(ids)

            sorted_relational_ids = {}
            for model_name, ids in relational_ids.items():
                if ids:
                    # Use search() to get IDs sorted by _order the same way Odoo ORM does for relational fields
                    sorted_relational_ids[model_name] = self.env[model_name].search([('id', 'in', list(ids))]).ids

            return sorted_relational_ids
        fields_to_fetch = list(set(ORDER_FIELDS_BEFORE_17_4) | set(ORDER_FIELDS_FROM_17_4))
        orders_data = self.read(fields_to_fetch + ['id'], load='')
        lines_data = self.lines.read(LINE_FIELDS + ['id', 'order_id'], load='')

        orders_by_id = {order['id']: order for order in orders_data}
        lines_by_order = defaultdict(list)
        for line in lines_data:
            lines_by_order[line['order_id']].append(line)
        order_field_defs = {
            field: {
                'type': self._fields[field].type,
                'comodel': self._fields[field].comodel_name if hasattr(self._fields[field], 'comodel_name') else None
            }
            for field in fields_to_fetch
        }
        line_field_defs = {
            field: {
                'type': self.lines._fields[field].type,
                'comodel': self.lines._fields[field].comodel_name if hasattr(self.lines._fields[field], 'comodel_name') else None
            }
            for field in LINE_FIELDS
        }

        sorted_relational_ids = collect_sorted_relational_ids(orders_data, lines_data, order_field_defs, line_field_defs)

        for order in self:
            values = {}
            if order.pos_version:
                order_fields = ORDER_FIELDS_FROM_17_4
            else:
                order_fields = ORDER_FIELDS_BEFORE_17_4
            for field in order_fields:
                values[field] = _getattrstring(order, field)
            order_data = orders_by_id[order.id]

            for field in order_fields:
                field_def = order_field_defs[field]
                values[field] = _getattrstring(order_data.get(field), field_def['type'], field_def['comodel'])

            for line in lines_by_order[order.id]:
                for field in LINE_FIELDS:
                    k = 'line_%d_%s' % (line['id'], field)
                    field_def = line_field_defs[field]
                    values[k] = _getattrstring(line.get(field), field_def['type'], field_def['comodel'])

            #make the json serialization canonical
            #  (https://tools.ietf.org/html/draft-staykov-hu-json-canonical-form-00)
            order.l10n_fr_string_to_hash = dumps(values, sort_keys=True,
                                                ensure_ascii=True, indent=None,
                                                separators=(',',':'))