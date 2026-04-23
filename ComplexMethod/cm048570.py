def _onchange_type(self):
        self.filtered(lambda journal: journal.type not in {'sale', 'purchase'}).alias_name = False
        for journal in self.filtered(lambda journal: (
            not journal.alias_name and journal.type in {'sale', 'purchase'})
        ):
            journal.alias_name = self._alias_prepare_alias_name(
                False, journal.name, journal.code, journal.type, journal.company_id)

        for journal in self:
            journal.code = False
            journal.default_account_id = False
            journal.profit_account_id = False
            journal.loss_account_id = False
            company = journal.company_id
            if journal.type == 'sale' and company.income_account_id.active:
                journal.default_account_id = company.income_account_id
            elif journal.type == 'purchase' and company.expense_account_id.active:
                journal.default_account_id = company.expense_account_id
            elif journal.type in ('cash', 'bank'):
                if company.default_cash_difference_income_account_id.active:
                    journal.profit_account_id = company.default_cash_difference_income_account_id
                if company.default_cash_difference_expense_account_id.active:
                    journal.loss_account_id = company.default_cash_difference_expense_account_id

        # codes are reset and recomputed whenever the
        # journal type changes through the form view
        self._compute_code()