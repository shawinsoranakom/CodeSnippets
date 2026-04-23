def _ensure_payment_method_line(self, allow_create=True):
        self.ensure_one()
        if not self.id:
            return

        default_payment_method = self._get_provider_payment_method(self._get_code())
        if not default_payment_method:
            return

        pay_method_line = self.env['account.payment.method.line'].search([
            ('payment_provider_id', '=', self.id),
            ('journal_id', '!=', False),
        ], limit=1)

        if not self.journal_id:
            if pay_method_line:
                pay_method_line.unlink()
                return

        if not pay_method_line:
            pay_method_line = self.env['account.payment.method.line'].search(
                [
                    *self.env['account.payment.method.line']._check_company_domain(self.company_id),
                    ('code', '=', self._get_code()),
                    ('payment_provider_id', '=', False),
                    ('journal_id', '!=', False),
                ],
                limit=1,
            )
        if pay_method_line:
            pay_method_line.payment_provider_id = self
            pay_method_line.journal_id = self.journal_id
            pay_method_line.name = self.name
        elif allow_create:
            create_values = {
                'name': self.name,
                'payment_method_id': default_payment_method.id,
                'journal_id': self.journal_id.id,
                'payment_provider_id': self.id,
                'payment_account_id': self._get_payment_method_outstanding_account_id(default_payment_method)
            }
            pay_method_line_same_code = self.env['account.payment.method.line'].search(
                [
                    *self.env['account.payment.method.line']._check_company_domain(self.company_id),
                    ('code', '=', self._get_code()),
                ],
                limit=1,
            )
            if pay_method_line_same_code:
                create_values['payment_account_id'] = pay_method_line_same_code.payment_account_id.id
            if self._get_code() == 'sepa_direct_debit':
                create_values['name'] = "Online SEPA"
            self.env['account.payment.method.line'].create(create_values)