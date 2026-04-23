def _fill_missing_values(self, vals, protected_codes=False):
        journal_type = vals.get('type')
        is_import = 'import_file' in self.env.context
        if is_import and not journal_type:
            vals['type'] = journal_type = 'general'

        # 'type' field is required.
        if not journal_type:
            return

        # === Fill missing company ===
        company = self.env['res.company'].browse(vals['company_id']) if vals.get('company_id') else self.env.company
        vals['company_id'] = company.id

        if journal_type in ('bank', 'cash'):
            has_liquidity_accounts = vals.get('default_account_id')
            has_profit_account = vals.get('profit_account_id')
            has_loss_account = vals.get('loss_account_id')

            # === Fill missing name ===
            vals['name'] = vals.get('name') or vals.get('bank_acc_number') or vals.get('name_placeholder')

            # === Fill missing accounts ===
            if not has_liquidity_accounts:
                vals['default_account_id'] = self._create_default_account(company, journal_type, vals)
            if journal_type in ('cash', 'bank') and not has_profit_account:
                vals['profit_account_id'] = company.default_cash_difference_income_account_id.id
            if journal_type in ('cash', 'bank') and not has_loss_account:
                vals['loss_account_id'] = company.default_cash_difference_expense_account_id.id

        if journal_type == 'credit':
            if not vals.get('default_account_id'):
                default_account_id = self.env['account.account'].with_company(company).search([
                        *self.env['account.account']._check_company_domain(company),
                        ('account_type', '=', 'liability_credit_card'),
                    ],
                    limit=1,
                ).id
                if not default_account_id:
                    default_account_id = self._create_default_account(company, journal_type, vals)
                vals['default_account_id'] = default_account_id

        if is_import and not vals.get('code'):
            code = vals['name'][:5]
            vals['code'] = code if not protected_codes or code not in protected_codes else self._get_next_journal_default_code(journal_type, company, protected_codes)
            if not vals['code']:
                raise UserError(_("Cannot generate an unused journal code. Please change the name for journal %s.", vals['name']))

        # === Fill missing alias name for sale / purchase, to force alias creation ===
        if journal_type in {'sale', 'purchase'}:
            if 'alias_name' not in vals:
                vals['alias_name'] = self._alias_prepare_alias_name(
                False, vals.get('name'), vals.get('code'), journal_type, company
            )
            vals['alias_name'] = self._ensure_unique_alias(vals, company)

        if not vals.get('name') and vals.get('name_placeholder'):
            vals['name'] = vals['name_placeholder']