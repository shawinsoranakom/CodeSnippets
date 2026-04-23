def _get_total_amount_in_wizard_currency(self):
        """
        Returns the total amount of the first batch, in the currency of the wizard.
        This information can be used to determine if we are doing a partial payment or not.
        """
        self.ensure_one()
        if not self.can_edit_wizard:
            return 0.0

        moves = self.batches[0]['lines'].move_id  # Use the move to get the TOTAL amount, including all installment.
        wizard_curr = self.currency_id
        comp_curr = self.company_currency_id

        total = 0.0
        for line in moves.line_ids.filtered(lambda batch_line: batch_line.display_type == 'payment_term'):
            currency = line.currency_id
            if currency == wizard_curr:
                # Same currency
                total += line.amount_currency
            elif currency != comp_curr and wizard_curr == comp_curr:
                # Foreign currency on source line but the company currency one on the opposite line.
                total += currency._convert(line.amount_currency, comp_curr, self.company_id, self.payment_date)
            elif currency == comp_curr and wizard_curr != comp_curr:
                # Company currency on source line but a foreign currency one on the opposite line.
                total += comp_curr._convert(line.balance, wizard_curr, self.company_id, self.payment_date)
            else:
                # Foreign currency on payment different from the one set on the journal entries.
                total += comp_curr._convert(line.balance, wizard_curr, self.company_id, self.payment_date)
        return total