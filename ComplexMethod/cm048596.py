def _setup_utility_bank_accounts(self, template_code, company, template_data):
        """Define basic bank accounts for the company.

        - Suspense Account
        - Outstanding Receipts/Payments Accounts
        - Cash Difference Gain/Loss Accounts
        - Liquidity Transfer Account
        """
        # Create utility bank_accounts
        bank_prefix = company.bank_account_code_prefix
        code_digits = int(template_data.get('code_digits', 6))
        accounts_data = self._get_accounts_data_values(company, template_data, bank_prefix=bank_prefix, code_digits=code_digits)
        for fname in list(accounts_data):
            if company[fname]:
                del accounts_data[fname]
        if company.parent_id:
            for company_attr_name in accounts_data:
                company[company_attr_name] = company.parent_ids[0][company_attr_name]
        else:
            accounts = self.env['account.account']._load_records([
                {
                    'xml_id': self.company_xmlid(xml_id, company),
                    'values': values,
                    'noupdate': True,
                }
                for xml_id, values in accounts_data.items()
            ])
            for company_attr_name, account in zip(accounts_data.keys(), accounts):
                company[company_attr_name] = account

        # No fields on company
        if not company.parent_id:
            self._create_outstanding_accounts(company, bank_prefix, code_digits)