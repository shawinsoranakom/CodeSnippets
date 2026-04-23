def write(self, vals):
        self._validate_locks(vals)

        self.env['res.company'].invalidate_model(fnames=[f'user_{field}' for field in LOCK_DATE_FIELDS if field in vals])

        # Reflect the change on accounts
        for company in self:
            if vals.get('bank_account_code_prefix'):
                new_bank_code = vals.get('bank_account_code_prefix') or company.bank_account_code_prefix
                company.reflect_code_prefix_change(company.bank_account_code_prefix, new_bank_code)

            if vals.get('cash_account_code_prefix'):
                new_cash_code = vals.get('cash_account_code_prefix') or company.cash_account_code_prefix
                company.reflect_code_prefix_change(company.cash_account_code_prefix, new_cash_code)

            # forbid the change of currency_id if there are already some accounting entries existing
            if 'currency_id' in vals and vals['currency_id'] != company.currency_id.id:
                if company.root_id._existing_accounting():
                    raise UserError(_('You cannot change the currency of the company since some journal items already exist'))

        companies = super().write(vals)

        self._set_category_defaults()
        # We revoke all active exceptions affecting the changed lock dates and recreate them (with the updated lock dates)
        changed_soft_lock_fields = [field for field in SOFT_LOCK_DATE_FIELDS if field in vals]
        for company in self:
            active_exceptions = self.env['account.lock_exception'].search(
                self.env['account.lock_exception']._get_active_exceptions_domain(company, changed_soft_lock_fields),
            )
            active_exceptions._recreate()

        return companies