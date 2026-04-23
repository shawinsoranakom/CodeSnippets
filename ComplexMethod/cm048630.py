def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        default = default or {}
        cache = defaultdict(set)

        for account, vals in zip(self, vals_list):
            company_ids = self._fields['company_ids'].convert_to_cache(vals['company_ids'], self.browse())
            companies = self.env['res.company'].browse(company_ids)

            if 'code_mapping_ids' not in default and ('code' not in default or len(companies) > 1):
                companies_to_get_new_account_codes = companies if 'code' not in default else companies[1:]
                vals['code_mapping_ids'] = []

                for company in companies_to_get_new_account_codes:
                    start_code = account.with_company(company).code or account.with_company(account.company_ids[0]).code
                    new_code = account.with_company(company)._search_new_account_code(start_code, cache[company.id])
                    vals['code_mapping_ids'].append(Command.create({'company_id': company.id, 'code': new_code}))
                    cache[company.id].add(new_code)

            if 'name' not in default:
                vals['name'] = self.env._("%s (copy)", account.name or '')

        return vals_list