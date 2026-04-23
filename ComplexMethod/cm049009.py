def _check_pos_order(self, pos_config, order, device_type, table=None):
        company = pos_config.company_id
        preset_id = order['preset_id'] if pos_config.use_presets else False
        preset_id = pos_config.env['pos.preset'].browse(preset_id) if preset_id else False
        floating_order_name = order.get('floating_order_name')

        if not preset_id and pos_config.use_presets:
            raise UserError(_("Invalid preset"))

        existing_order = pos_config.env['pos.order']._get_open_order(order)
        if not existing_order.exists():
            pos_reference, tracking_number = pos_config._get_next_order_refs()
            prefix = f"K{pos_config.id}-" if device_type == "kiosk" else "S"

            if device_type == 'kiosk':
                floating_order_name = f"Table tracker {order['table_stand_number']}" if order.get('table_stand_number') else tracking_number
            elif not floating_order_name:
                floating_order_name = f"Self-Order T {table.table_number}" if table else f"Self-Order {tracking_number}"

            tracking_number = f"{prefix}{tracking_number}"
        else:
            pos_reference = existing_order.pos_reference
            floating_order_name = existing_order.floating_order_name
            tracking_number = existing_order.tracking_number

        fiscal_position_id = preset_id.fiscal_position_id if preset_id else pos_config.default_fiscal_position_id
        pricelist_id = preset_id.pricelist_id if preset_id else pos_config.pricelist_id
        lines = [self._check_pos_order_lines(pos_config, order, line, fiscal_position_id) for line in order.get('lines', [])]
        lines = [line for line in lines if len(line)]
        partner_id = order.get('partner_id')
        partner = pos_config.env['res.partner'].browse(partner_id) if partner_id else None

        return {
            'id': order.get('id'),
            'table_stand_number': order.get('table_stand_number'),
            'access_token': order.get('access_token'),
            'customer_count': order.get('customer_count'),
            'self_ordering_table_id': table.id if table else False,
            'last_order_preparation_change': order.get('last_order_preparation_change'),
            'date_order': str(fields.Datetime.now()),
            'amount_difference': order.get('amount_difference'),
            'amount_tax': order.get('amount_tax'),
            'amount_total': order.get('amount_total'),
            'amount_paid': order.get('amount_paid'),
            'amount_return': order.get('amount_return'),
            'company_id': company.id,
            'pricelist_id': pricelist_id.id if pricelist_id else False,
            'partner_id': order.get('partner_id'),
            'sequence_number': order.get('sequence_number'),
            'session_id': pos_config.current_session_id.id,
            'fiscal_position_id': fiscal_position_id.id if fiscal_position_id else False,
            'preset_id': preset_id.id if preset_id else False,
            'preset_time': order.get('preset_time'),
            'tracking_number': tracking_number,
            'source': 'kiosk' if device_type == 'kiosk' else 'mobile',
            'email': partner.email if partner else order.get('email'),
            'mobile': order.get('mobile'),
            'state': order.get('state'),
            'account_move': order.get('account_move'),
            'floating_order_name': floating_order_name,
            'general_customer_note': order.get('general_customer_note'),
            'nb_print': order.get('nb_print'),
            'pos_reference': pos_reference,
            'to_invoice': order.get('to_invoice'),
            'shipping_date': order.get('shipping_date'),
            'is_tipped': order.get('is_tipped'),
            'tip_amount': order.get('tip_amount'),
            'ticket_code': order.get('ticket_code'),
            'uuid': order.get('uuid'),
            'has_deleted_line': order.get('has_deleted_line'),
            'lines': lines,
            'relations_uuid_mapping': order.get('relations_uuid_mapping', {}),
        }