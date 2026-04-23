def _post_load_data(self, template_code, company, template_data):
        company = (company or self.env.company)
        additional_properties = template_data.pop('additional_properties', {})

        self._setup_utility_bank_accounts(template_code, company, template_data)

        # Unaffected earnings account on the company (if not present yet)
        company.get_unaffected_earnings_account()

        # Set newly created Cash difference and Suspense accounts to the Cash and Bank journals
        for journal in self.env['account.journal'].search([('type', 'in', ['cash', 'bank', 'credit']), ('company_id', '=', company.id)]):
            if journal:
                journal.suspense_account_id = journal.suspense_account_id or company.account_journal_suspense_account_id
                journal.profit_account_id = journal.profit_account_id or company.default_cash_difference_income_account_id
                journal.loss_account_id = journal.loss_account_id or company.default_cash_difference_expense_account_id

        # Set newly created journals as defaults for the company
        if not company.tax_cash_basis_journal_id:
            company.tax_cash_basis_journal_id = self.ref('caba', raise_if_not_found=False)
        if not company.currency_exchange_journal_id:
            company.currency_exchange_journal_id = self.ref('exch', raise_if_not_found=False)

        # Setup default Income/Expense Accounts on Sale/Purchase journals
        sale_journal = self.ref("sale", raise_if_not_found=False)
        if sale_journal and company.income_account_id:
            sale_journal.default_account_id = company.income_account_id
        purchase_journal = self.ref("purchase", raise_if_not_found=False)
        if purchase_journal and company.expense_account_id:
            purchase_journal.default_account_id = company.expense_account_id

        # Set default Purchase and Sale taxes on the company
        if not company.account_sale_tax_id:
            company.account_sale_tax_id = self.env['account.tax'].search([
                *self.env['account.tax']._check_company_domain(company),
                ('type_tax_use', 'in', ('sale', 'all'))], limit=1).id
        if not company.account_purchase_tax_id:
            company.account_purchase_tax_id = self.env['account.tax'].search([
                *self.env['account.tax']._check_company_domain(company),
                ('type_tax_use', 'in', ('purchase', 'all'))], limit=1).id
        # Set default taxes on products (only on products having already a tax set in another company, as some flows require no tax at all (e.g TIPS in PoS))
        # We need to browse the product in sudo to check for the taxes_id and supplier_taxes_id fields regardless of the companies record rules
        # that would, otherwise, just look empty all the time for the current user/company
        company_domain = self.env['product.template']._check_company_domain(company)
        if company.account_sale_tax_id:
            sudoed_products_sale = self.env['product.template'].sudo().search(
                Domain.AND([
                    company_domain,
                    Domain('taxes_id', '!=', False),
                    Domain('taxes_id', 'not any', company_domain),
                ])
            )
            sudoed_products_sale._force_default_sale_tax(company)
        if company.account_purchase_tax_id:
            sudoed_products_purchase = self.env['product.template'].sudo().search(
                Domain.AND([
                    company_domain,
                    Domain('supplier_taxes_id', '!=', False),
                    Domain('supplier_taxes_id', 'not any', company_domain),
                ])
            )
            sudoed_products_purchase._force_default_purchase_tax(company)

        # Display caba fields if there are caba taxes
        if not company.parent_id and self.env['account.tax'].search_count([('tax_exigibility', '=', 'on_payment')], limit=1):
            company.tax_exigibility = True

        for field, model in self._get_property_accounts(additional_properties).items():
            value = template_data.get(field)
            if value and field in self.env[model]._fields:
                self.env['ir.default'].set(model, field, self.ref(value).id, company_id=company.id)

        # Set default Income/Expense Accounts on Product Category Property from Company
        self.env['ir.default'].set(
            'product.category',
            'property_account_income_categ_id',
            company.income_account_id.id,
            company_id=company.id,
        )
        self.env['ir.default'].set(
            'product.category',
            'property_account_expense_categ_id',
            company.expense_account_id.id,
            company_id=company.id,
        )

        # Set default transfer account on the internal transfer reconciliation model
        reco = self.ref('internal_transfer_reco', raise_if_not_found=False)
        if reco:
            reco.line_ids.sudo().write({'account_id': company.transfer_account_id.id})

        bank_fees = self.ref('bank_fees_reco', raise_if_not_found=False)
        if bank_fees:
            bank_fees.line_ids.sudo().write({'account_id': self._get_bank_fees_reco_account(company).id})

        company._initiate_account_onboardings()