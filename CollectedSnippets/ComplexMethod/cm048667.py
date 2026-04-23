def _get_quick_edit_suggestions(self):
        """
        Returns a dictionnary containing the suggested values when creating a new
        line with the quick_edit_total_amount set. We will compute the price_unit
        that has to be set with the correct that in order to match this total amount.
        If the vendor/customer is set, we will suggest the most frequently used account
        for that partner as the default one, otherwise the default of the journal.
        """
        self.ensure_one()
        if not self.quick_edit_mode or not self.quick_edit_total_amount:
            return False
        count, account_id, tax_ids = self._get_frequent_account_and_taxes(
            self.company_id.id,
            self.partner_id.id,
            self.move_type,
        )
        if count:
            taxes = self.env['account.tax'].browse(tax_ids)
        else:
            account_id = self.journal_id.default_account_id.id
            if self.is_sale_document(include_receipts=True):
                taxes = self.journal_id.default_account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'sale')
            else:
                taxes = self.journal_id.default_account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'purchase')
            if not taxes:
                taxes = (
                    self.journal_id.company_id.account_sale_tax_id
                    if self.journal_id.type == 'sale' else
                    self.journal_id.company_id.account_purchase_tax_id
                )
            taxes = self.fiscal_position_id.map_tax(taxes)

        # When a payment term has an early payment discount with the epd computation set to 'mixed', recomputing
        # the untaxed amount should take in consideration the discount percentage otherwise we'd get a wrong value.
        # We check that we have only one percentage tax as computing from multiple taxes with different types can get complicated.
        # In one example: let's say: base = 100, discount = 2%, tax = 21%
        # the total will be calculated as: total = base + (base * (1 - discount)) * tax
        # If we manipulate the equation to get the base from the total, we'll have base = total / ((1 - discount) * tax + 1)
        term = self.invoice_payment_term_id
        discount_percentage = term.discount_percentage if term.early_discount else 0
        remaining_amount = self.quick_edit_total_amount - self.tax_totals['total_amount_currency']

        if (
                discount_percentage
                and term.early_pay_discount_computation == 'mixed'
                and len(taxes) == 1
                and taxes.amount_type == 'percent'
        ):
            price_untaxed = self.currency_id.round(
                remaining_amount / (((1.0 - discount_percentage / 100.0) * (taxes.amount / 100.0)) + 1.0))
        else:
            price_untaxed = taxes.with_context(force_price_include=True).compute_all(remaining_amount)['total_excluded']
        return {'account_id': account_id, 'tax_ids': taxes.ids, 'price_unit': price_untaxed}