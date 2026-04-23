def _compute_prices(self):
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.currency_id:
                raise UserError(_("You can't: create a pos order from the backend interface, or unset the pricelist, or create a pos.order in a python test with Form tool, or edit the form view in studio if no PoS order exist"))
            order.amount_paid = sum(payment.amount for payment in order.payment_ids)
            order.amount_return = -sum(payment.amount < 0 and payment.amount or 0 for payment in order.payment_ids)

            base_lines = order.lines._prepare_tax_base_line_values()
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)

            cash_rounding = None
            if (
                order.config_id.cash_rounding
                and not order.config_id.only_round_cash_method
                and order.config_id.rounding_method
            ):
                cash_rounding = order.config_id.rounding_method

            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id,
                company=order.company_id,
                cash_rounding=cash_rounding,
            )
            refund_factor = -1 if (order.is_refund or order.amount_total < 0.0) else 1
            order.amount_tax = refund_factor * tax_totals['tax_amount_currency']
            order.amount_total = refund_factor * tax_totals['total_amount_currency']
            order.amount_difference = order.amount_paid - order.amount_total