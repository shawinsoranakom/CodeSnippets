def create(self, vals_list):
        journals = super().create(vals_list)
        inbound_payment_accounts = self.env['account.account'].search([
            ('code', '=', '1.1.1.02.003'),
            ('company_ids', 'in', journals.company_id.ids)
        ]).grouped('company_ids')

        outbound_payment_accounts = self.env['account.account'].search([
            ('code', '=', '1.1.1.02.004'),
            ('company_ids', 'in', journals.company_id.ids)
        ]).grouped('company_ids')

        for journal in journals:
            if journal.country_code != 'AR' or journal.type not in ('bank', 'cash'):
                continue

            for payment_method_line in journal.inbound_payment_method_line_ids:
                if payment_method_line.payment_account_id:
                    continue
                payment_method_line.payment_account_id = inbound_payment_accounts.get(journal.company_id)

            for payment_method_line in journal.outbound_payment_method_line_ids:
                if payment_method_line.payment_account_id:
                    continue
                payment_method_line.payment_account_id = outbound_payment_accounts.get(journal.company_id)

        return journals