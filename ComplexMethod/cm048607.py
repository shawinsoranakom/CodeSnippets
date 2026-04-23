def _compute_journal_id(self):
        for payment in self:
            # default customer payment method logic
            partner = payment.partner_id
            payment_type = payment.payment_type if payment.payment_type in ('inbound', 'outbound') else None
            if not bool(payment._origin) and (partner or payment_type):
                field_name = f'property_{payment_type}_payment_method_line_id'
                default_payment_method_line = payment.partner_id.with_company(payment.company_id)[field_name]
                journal = default_payment_method_line.journal_id
                if journal:
                    payment.journal_id = journal
                    continue

            company = payment.company_id or self.env.company
            if not payment.journal_id or company != payment.journal_id.company_id:
                payment.journal_id = self.env['account.journal'].search([
                    *self.env['account.journal']._check_company_domain(company),
                    ('type', 'in', ['bank', 'cash', 'credit']),
                ], limit=1)