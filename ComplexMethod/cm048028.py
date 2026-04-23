def _process_order(self, order, existing_order):
        """ There are a few cases where we want to block the creation of the order to maintain correct data for the EDI. """
        # Start by looking in the data to see if we have any refund lines; and if so we want to gather all refunded orders.
        session = self.env['pos.session'].browse(order['session_id'])
        if not session.config_id.company_id._l10n_my_edi_enabled():
            return super()._process_order(order, existing_order)

        refunded_order_line_ids = []
        for line in order['lines']:
            line_data = line[-1]
            if not line_data.get('refunded_orderline_id'):
                continue
            refunded_order_line_ids.append(line_data['refunded_orderline_id'])

        refunded_orders = self.env['pos.order.line'].browse(refunded_order_line_ids).order_id
        if not refunded_orders:  # Nothing more to do for now.
            return super()._process_order(order, existing_order)

        # If the order contains refund lines, we need to assert that we invoice (or not) the order based on the state of
        # the orders being refunded.
        to_invoice = order.get('to_invoice')

        for refunded_order in refunded_orders:
            submitted = ((refunded_order.is_invoiced and refunded_order.account_move.l10n_my_edi_state in ["in_progress", "valid", "rejected"])
                         or (refunded_order._get_active_consolidated_invoice() and refunded_order._get_active_consolidated_invoice().myinvois_state in ["in_progress", "valid", "rejected"]))

            if submitted and not to_invoice:
                raise UserError(refunded_order.env._('You must invoice a refund for an order that has been submitted to MyInvois.'))
            if not submitted and to_invoice:
                raise UserError(refunded_order.env._('You cannot invoice a refund for an order that has not been submitted to MyInvois yet.'))

            if refunded_order._get_active_consolidated_invoice():
                if not to_invoice:
                    # When we refund an order which is included in a not-yet-sent consolidated invoice, we link the refund to it.
                    order['consolidated_invoice_ids'] = refunded_order._get_active_consolidated_invoice().id

        return super()._process_order(order, existing_order)