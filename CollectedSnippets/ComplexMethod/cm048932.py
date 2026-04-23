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