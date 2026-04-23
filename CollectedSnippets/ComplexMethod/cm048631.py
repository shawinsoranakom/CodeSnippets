def create(self, vals_list):
        records_list = []

        for company_ids, vals_list_for_company in itertools.groupby(vals_list, lambda v: v.get('company_ids', [])):
            cache = set()
            vals_list_for_company = list(vals_list_for_company)

            # Determine the companies the new accounts will have.
            company_ids = self._fields['company_ids'].convert_to_cache(company_ids, self.browse())
            companies = self.env['res.company'].browse(company_ids)
            if self.env.company in companies or not companies:
                companies = self.env.company | companies  # The currently active company comes first.

            for vals in vals_list_for_company:
                if 'prefix' in vals:
                    prefix = vals.pop('prefix') or ''
                    digits = vals.pop('code_digits')
                    start_code = prefix.ljust(digits - 1, '0') + '1' if len(prefix) < digits else prefix
                    vals['code'] = self.with_company(companies[0])._search_new_account_code(start_code, cache)
                    cache.add(vals['code'])

                if 'code' not in vals:  # prepopulate the code for precomputed fields depending on it
                    for mapping_command in vals.get('code_mapping_ids', []):
                        match mapping_command:
                            case Command.CREATE, _, {'company_id': company_id, 'code': code} if company_id == companies[0].id:
                                vals['code'] = code
                                break

            new_accounts = super(AccountAccount, self.with_context(
                allowed_company_ids=companies.ids,
                defer_account_code_checks=True,
                # Don't get a default value for `code_mapping_ids` from default_get
                default_code_mapping_ids=self.env.context.get('default_code_mapping_ids', []),
            )).create(vals_list_for_company)

            records_list.append(new_accounts)

        records = self.env['account.account'].union(*records_list)
        records._ensure_code_is_unique()
        return records