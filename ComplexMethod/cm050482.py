def _create_journal_and_payment_methods(self, cash_ref=None, cash_journal_vals=None):
        """This should only be called at creation of a new pos.config."""

        journal = self.env['account.journal']._ensure_company_account_journal()
        payment_methods = self.env['pos.payment.method']

        # create cash payment method per config
        cash_pm_from_ref = cash_ref and self.env.ref(cash_ref, raise_if_not_found=False)
        if cash_pm_from_ref:
            try:
                cash_pm_from_ref.check_access('read')
                cash_pm = cash_pm_from_ref
            except AccessError:
                cash_pm = self._create_cash_payment_method(cash_journal_vals)
        else:
            cash_pm = self._create_cash_payment_method(cash_journal_vals)

        if cash_ref and cash_pm != cash_pm_from_ref:
            self.env['ir.model.data']._update_xmlids([{
                'xml_id': cash_ref,
                'record': cash_pm,
                'noupdate': True,
            }])

        payment_methods |= cash_pm

        # only create bank and customer account payment methods per company
        bank_pm = self.env['pos.payment.method'].search([('journal_id.type', '=', 'bank'), ('company_id', 'in', self.env.company.parent_ids.ids)])
        if not bank_pm:
            bank_journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', 'in', self.env.company.parent_ids.ids)], limit=1)
            if not bank_journal:
                raise UserError(_('Ensure that there is an existing bank journal. Check if chart of accounts is installed in your company.'))
            chart_template = self.with_context(allowed_company_ids=self.env.company.root_id.ids).env['account.chart.template']
            outstanding_account = chart_template.ref('account_journal_payment_debit_account_id', raise_if_not_found=False) or self.env.company.transfer_account_id
            bank_pm = self.env['pos.payment.method'].create({
                'name': _('Card'),
                'journal_id': bank_journal.id,
                'outstanding_account_id': outstanding_account.id if outstanding_account else False,
                'company_id': self.env.company.id,
                'sequence': 1,
            })

        payment_methods |= bank_pm

        pay_later_pm = self.env['pos.payment.method'].search([('journal_id', '=', False), ('company_id', 'in', self.env.company.parent_ids.ids)])
        if not pay_later_pm:
            pay_later_pm = self.env['pos.payment.method'].create({
                'name': _('Customer Account'),
                'company_id': self.env.company.id,
                'split_transactions': True,
                'sequence': 2,
            })

        payment_methods |= pay_later_pm

        return journal, payment_methods.ids