def _get_partner_bank_id(self):
        partner_bank_id = False
        amount_total = sum(order.amount_total for order in self)

        def _first_allowed(bank_ids):
            return bank_ids.filtered(lambda b: b.allow_out_payment)[:1]

        # Case 1: refund / negative amount → customer bank
        if amount_total <= 0 and self.partner_id.bank_ids:
            partner_bank_id = _first_allowed(self.partner_id.bank_ids)

        # Case 2: positive amount → payment journal bank
        elif amount_total >= 0 and self.payment_ids:
            journal_bank = self.payment_ids[0].payment_method_id.journal_id.bank_account_id
            if journal_bank and journal_bank.allow_out_payment:
                partner_bank_id = journal_bank

        # Case 3: fallback → company bank
        if not partner_bank_id and amount_total >= 0 and self.company_id.partner_id.bank_ids:
            partner_bank_id = _first_allowed(self.company_id.partner_id.bank_ids)

        return partner_bank_id.id if partner_bank_id else False