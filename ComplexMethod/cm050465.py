def _prepare_invoice_vals(self):
        """We have orders filtered by company > config > partners > fiscal_positions so it won't make any issue
        when we access user, partner, bank or similar directly.
        """
        timezone = self.env.tz
        invoice_date = fields.Datetime.now()
        is_single_order = len(self) == 1

        if is_single_order and self.session_id.state != 'closed':
            invoice_date = self.date_order

        pos_refunded_invoice_ids = []
        for orderline in self.lines:
            if orderline.refunded_orderline_id and orderline.refunded_orderline_id.order_id.account_move:
                pos_refunded_invoice_ids.append(orderline.refunded_orderline_id.order_id.account_move.id)

        fiscal_position = self.fiscal_position_id
        pos_config = self.config_id
        move_type = 'out_invoice' if not any(
            order.is_refund or order.amount_total < 0.0 for order in self
        ) else 'out_refund'
        invoice_payment_term_id = (
            self.partner_id.property_payment_term_id.id
            if self.partner_id.property_payment_term_id and any(p.payment_method_id.type == 'pay_later' for p in self.payment_ids)
            else False
        )

        vals = {
            'invoice_origin': ', '.join(ref or '' for ref in self.mapped('pos_reference')),
            'pos_refunded_invoice_ids': pos_refunded_invoice_ids,
            'pos_order_ids': self.ids,
            'ref': self.name if is_single_order else False,
            'journal_id': self.config_id.invoice_journal_id.id,
            'move_type': move_type,
            'partner_id': self.partner_id.address_get(['invoice'])['invoice'],
            'partner_shipping_id': self.partner_id.address_get(['delivery'])['delivery'],
            'partner_bank_id': self._get_partner_bank_id(),
            'currency_id': self.currency_id.id,
            'invoice_date': invoice_date.astimezone(timezone).date(),
            'invoice_user_id': self.user_id.id,
            'fiscal_position_id': fiscal_position.id,
            'invoice_line_ids': self._prepare_invoice_lines(move_type),
            'invoice_payment_term_id': invoice_payment_term_id,
        }
        if is_single_order and self.refunded_order_id.account_move:
            vals['ref'] = _('Reversal of: %s', self.refunded_order_id.account_move.name)
            vals['reversed_entry_id'] = self.refunded_order_id.account_move.id

        if pos_config.cash_rounding and (not pos_config.only_round_cash_method or any(p.payment_method_id.is_cash_count for p in self.payment_ids)):
            vals['invoice_cash_rounding_id'] = pos_config.rounding_method.id

        if any(order.floating_order_name for order in self):
            vals.update({'narration': ', '.join(self.filtered('floating_order_name').mapped('floating_order_name'))})

        return vals