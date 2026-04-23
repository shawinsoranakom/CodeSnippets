def get_orders_by_access_token(self, access_token, order_access_tokens, table_identifier=None):
        pos_config = self._verify_pos_config(access_token)
        table = pos_config.env["restaurant.table"].search([('identifier', '=', table_identifier)], limit=1)
        domain = False

        if not table_identifier or pos_config.self_ordering_pay_after == 'each':
            domain = [(False, '=', True)]
        else:
            domain = ['&', '&',
                ('table_id', '=', table.id),
                ('state', '=', 'draft'),
                ('access_token', 'not in', [data.get('access_token') for data in order_access_tokens])
            ]

        for data in order_access_tokens:
            domain = Domain.OR([domain, ['&',
                ('access_token', '=', data['access_token']),
                '|',
                ('write_date', '>', data.get('write_date')),
                ('state', '!=', data.get('state')),
            ]])
        orders = pos_config.env['pos.order'].search(domain)

        access_tokens = set({o.get('access_token') for o in order_access_tokens})
        # Do not use session.order_ids, it may fail if there is shared sessions
        existing_order_tokens = pos_config.env['pos.order'].search([('access_token', 'in', access_tokens)]).mapped('access_token')
        if deleted_order_tokens := list(access_tokens - set(existing_order_tokens)):
            # Remove orders that no longer exist on the server but are still shown in the self-order UI
            pos_config._notify('REMOVE_ORDERS', {'deleted_order_tokens': deleted_order_tokens})
        return self._generate_return_values(orders, pos_config) if orders else {}