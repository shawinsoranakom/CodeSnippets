def _convert_to_wizard_currency(self, installments):
        self.ensure_one()
        total_per_currency = defaultdict(lambda: {
            'amount_residual': 0.0,
            'amount_residual_currency': 0.0,
        })
        for installment in installments:
            line = installment['line']
            total_per_currency[line.currency_id]['amount_residual'] += installment['amount_residual']
            total_per_currency[line.currency_id]['amount_residual_currency'] += installment['amount_residual_currency']

        total_amount = 0.0
        wizard_curr = self.currency_id
        comp_curr = self.company_currency_id
        for currency, amounts in total_per_currency.items():
            amount_residual = amounts['amount_residual']
            amount_residual_currency = amounts['amount_residual_currency']
            if currency == wizard_curr:
                # Same currency
                total_amount += amount_residual_currency
            elif currency != comp_curr and wizard_curr == comp_curr:
                # Foreign currency on source line but the company currency one on the opposite line.
                total_amount += currency._convert(amount_residual_currency, comp_curr, self.company_id, self.payment_date)
            elif currency == comp_curr and wizard_curr != comp_curr:
                # Company currency on source line but a foreign currency one on the opposite line.
                total_amount += comp_curr._convert(amount_residual, wizard_curr, self.company_id, self.payment_date)
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                total_amount += comp_curr._convert(amount_residual, wizard_curr, self.company_id, self.payment_date)
        return total_amount