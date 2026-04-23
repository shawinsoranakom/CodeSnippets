def _check_pos_order_lines(self, pos_config, order, line, fiscal_position_id):
        existing_order = pos_config.env['pos.order']._get_open_order(order)
        existing_lines = existing_order.lines if existing_order.exists() else pos_config.env['pos.order.line']

        if line[0] == Command.DELETE and line[1] in existing_lines.ids:
            return [Command.DELETE, line[1]]
        if line[0] == Command.UNLINK and line[1] in existing_lines.ids:
            return [Command.UNLINK, line[1]]
        if line[0] == Command.CREATE or line[0] == Command.UPDATE:
            line_data = line[2]

            product = pos_config.env['product.product'].browse(line_data.get('product_id'))
            tax_ids = fiscal_position_id.map_tax(product.taxes_id)
            command = Command.CREATE if line[0] == Command.CREATE else Command.UPDATE
            id_to_use = line[1] if line[0] == Command.UPDATE else 0

            return [command, id_to_use, {
                'combo_id': line_data.get('combo_id'),
                'product_id': line_data.get('product_id'),
                'tax_ids': tax_ids.ids,
                'attribute_value_ids': [id for id in line_data.get('attribute_value_ids', []) if isinstance(id, int)],
                'price_unit': line_data.get('price_unit'),
                'qty': line_data.get('qty'),
                'price_subtotal': line_data.get('price_subtotal'),
                'price_subtotal_incl': line_data.get('price_subtotal_incl'),
                'price_extra': line_data.get('price_extra'),
                'price_type': line_data.get('price_type'),
                'full_product_name': line_data.get('full_product_name'),
                'customer_note': line_data.get('customer_note'),
                'uuid': line_data.get('uuid'),
                'id': line_data.get('id'),
                'order_id': existing_order.id if existing_order.exists() else None,
                'combo_parent_id': line_data.get('combo_parent_id'),
                'combo_item_id': line_data.get('combo_item_id'),
                'combo_line_ids': [id for id in line_data.get('combo_line_ids', []) if isinstance(id, int)],
            }]
        return []