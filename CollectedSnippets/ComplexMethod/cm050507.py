def _onchange_journal_id(self):
        for pm in self:
            if pm.journal_id and pm.journal_id.type not in ['cash', 'bank']:
                raise UserError(_("Only journals of type 'Cash' or 'Bank' could be used with payment methods."))
            if pm.journal_id and pm.journal_id.type == 'bank':
                chart_template = self.with_context(allowed_company_ids=self.env.company.root_id.ids).env['account.chart.template']
                pm.outstanding_account_id = chart_template.ref('account_journal_payment_debit_account_id', raise_if_not_found=False) or self.company_id.transfer_account_id
        if self.is_cash_count:
            self.use_payment_terminal = False