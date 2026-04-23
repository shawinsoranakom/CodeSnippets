def _prepare_withhold_move_lines(self, withholding_account_id):
        """
        Prepare the move lines for the withhold entry
        """
        def append_vals(quantity, price_unit, debit, credit, account_id, tax_ids):
            return {
                'quantity': quantity,
                'price_unit': price_unit,
                'debit': debit,
                'credit': credit,
                'account_id': account_id.id,
                'tax_ids': tax_ids,
            }

        vals = []

        partner = self.related_move_id.partner_id or self.related_payment_id.partner_id
        withhold_type = self._get_withhold_type()

        if withhold_type in ('in_withhold', 'in_refund_withhold'):
            partner_account = partner.property_account_payable_id
        else:
            partner_account = partner.property_account_receivable_id

        # Create move line for withholding tax and the base amount
        debit = self.base if withhold_type in ('in_withhold', 'out_refund_withhold') else 0.0
        credit = 0.0 if withhold_type in ('in_withhold', 'out_refund_withhold') else self.base
        vals.append(append_vals(1.0, self.base, debit, credit, withholding_account_id, [Command.set(self.tax_id.ids)]))
        total_amount = self.base
        total_tax = self.amount

        # Create move line for the base amount
        debit = 0.0 if withhold_type in ('in_withhold', 'out_refund_withhold') else total_amount
        credit = total_amount if withhold_type in ('in_withhold', 'out_refund_withhold') else 0.0
        vals.append(append_vals(1.0, total_amount, debit, credit, withholding_account_id, False))

        # Create move line for the tax amount
        debit = total_tax if withhold_type in ('in_withhold', 'out_refund_withhold') else 0.0
        credit = 0.0 if withhold_type in ('in_withhold', 'out_refund_withhold') else total_tax
        vals.append(append_vals(1.0, total_tax, debit, credit, partner_account, False))

        return vals