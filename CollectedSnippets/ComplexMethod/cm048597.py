def _instantiate_foreign_taxes(self, country, company):
        """Create and configure foreign taxes from the provided country.

        Instantiate the taxes as they would be for the foreign localization only replacing the accounts used by the most
        probable account we can retrieve from the company's localization.
        This method is intended as a shortcut for instantiation, accelerating it, not as an out-of-the-box solution 100%
        correct solution.
        """
        # Implementation:
        # - Check if there is any tax for this country and stop the process if yes
        # - Retrieve the tax group and tax template data
        # - Try to create accounts at most probable location in the CoA
        # - Assign those accounts to the data
        # - Creates tax group and taxes with their ir.model.data

        taxes_in_country = self.env['account.tax'].search([
            *self.env['account.tax']._check_company_domain(company),
            ('country_id', '=', country.id),
        ])
        if taxes_in_country:
            return

        def create_foreign_tax_account(existing_account, additional_label, reconcilable=False):
            new_code = self.env['account.account'].with_company(company)._search_new_account_code(existing_account.code)
            return self.env['account.account'].create({
                'name': f"{existing_account.name} - {additional_label}",
                'code': new_code,
                'account_type': existing_account.account_type,
                'reconcile': reconcilable or existing_account.reconcile,
                'non_trade': existing_account.non_trade,
                'company_ids': [Command.link(company.id)],
            })

        existing_accounts = {'': None, None: None}  # keeps tracks of the created account by foreign xml_id
        default_company_taxes = company.account_sale_tax_id + company.account_purchase_tax_id
        chart_template_code = self._guess_chart_template(country=country)
        tax_group_data = self._get_chart_template_data(chart_template_code)['account.tax.group']
        tax_data = self._get_chart_template_data(chart_template_code)['account.tax']

        # Populate foreign accounts mapping
        # Try to create tax group accounts if not mapped
        field_and_names = (
            ('tax_payable_account_id', _("Foreign tax account payable (%s)", country.code)),
            ('tax_receivable_account_id', _("Foreign tax account receivable (%s)", country.code)),
            ('advance_tax_payment_account_id', _("Foreign tax account advance payment (%s)", country.code)),
        )
        for field, account_name in field_and_names:
            for tax_group in tax_group_data.values():
                account_template_xml_id = tax_group.get(field)
                if account_template_xml_id in existing_accounts:
                    continue
                local_tax_group = self.env["account.tax.group"].search([
                    *self.env['account.tax.group']._check_company_domain(company),
                    ('country_id', '=', company.account_fiscal_country_id.id),
                    (field, '!=', False),
                ], limit=1)
                if local_tax_group:
                    existing_accounts[account_template_xml_id] = create_foreign_tax_account(local_tax_group[field], account_name).id

        # Try to create repartition lines account if not mapped
        for tax_template in tax_data.values():
            for _command, _id, rep_line in tax_template.get('repartition_line_ids', []):
                if 'account_id' in rep_line and rep_line['repartition_type'] == 'tax':
                    type_tax_use, foreign_tax_rep_line = tax_template['type_tax_use'], rep_line
                    account_template_xml_id = foreign_tax_rep_line['account_id']
                    if account_template_xml_id in existing_accounts:
                        continue

                    sign_comparator = '<' if float(foreign_tax_rep_line.get('factor_percent', 100)) < 0 else '>'
                    minimal_domain = [
                        *self.env['account.tax.repartition.line']._check_company_domain(company),
                        ('account_id', '!=', False),
                        ('factor_percent', sign_comparator, 0),
                    ]
                    additional_domain = [
                        ('tax_id.type_tax_use', '=', type_tax_use),
                        ('tax_id.country_id', '=', company.account_fiscal_country_id.id),
                        ('tax_id', 'in', default_company_taxes.ids),
                    ]

                    # Trying to find an account being less restrictive on each iteration until the minimum acceptable is
                    # reached. If nothing is found, don't fill it to avoid setting a wrong account
                    similar_repartition_line = None
                    while not similar_repartition_line and additional_domain:
                        search_domain = minimal_domain + additional_domain
                        similar_repartition_line = self.env['account.tax.repartition.line'].search(search_domain, limit=1)
                        additional_domain.pop()

                    if similar_repartition_line:
                        local_tax_account = similar_repartition_line.account_id
                        similar_account_id = create_foreign_tax_account(local_tax_account, _("Foreign tax account (%s)", country.code))
                        existing_accounts[account_template_xml_id] = similar_account_id.id

        # Try to create cash basis account if not mapped
        local_cash_basis_tax = self.env["account.tax"].search([
            *self.env['account.tax']._check_company_domain(company),
            ('country_id', '=', company.account_fiscal_country_id.id),
            ('tax_exigibility', '=', 'on_payment'),
            ('cash_basis_transition_account_id', '!=', False)
        ], limit=1)
        has_cash_basis = False
        for tax_template in sorted(tax_data.values(), key=lambda x: any(rep_line.get('account_id') for _command, _id, rep_line in x.get('repartition_line_ids', [])), reverse=True):
            if tax_template.get('tax_exigibility') == 'on_payment':
                has_cash_basis = True

                account_xml_id = tax_template.get('cash_basis_transition_account_id')
                if account_xml_id not in existing_accounts:
                    if local_cash_basis_tax:
                        existing_accounts[account_xml_id] = create_foreign_tax_account(
                            local_cash_basis_tax.cash_basis_transition_account_id,
                            _("Cash basis transition account"),
                            reconcilable=True,
                        ).id

                    elif account_ids := [rep_line['account_id'] for _command, _id, rep_line in tax_template.get('repartition_line_ids', []) if rep_line.get('account_id')]:
                        local_account = self.env['account.account'].browse(existing_accounts[account_ids[0]])
                        existing_accounts[account_xml_id] = create_foreign_tax_account(local_account, _("Cash basis transition account"), reconcilable=True).id

                    else:
                        existing_accounts[account_xml_id] = None

        if has_cash_basis:
            company.tax_exigibility = True

        # Assign the account based on the map
        for field, _account_name in field_and_names:
            for tax_group in tax_group_data.values():
                tax_group[field] = existing_accounts.get(tax_group.get(field))

        for tax_template in tax_data.values():
            # This is required because the country isn't provided directly by the template
            tax_template['country_id'] = country.id

            if tax_template.get('tax_group_id'):
                tax_template['tax_group_id'] = f"{chart_template_code}_{tax_template['tax_group_id']}"

            for _command, _id, rep_line in tax_template.get('repartition_line_ids', []):
                rep_line['account_id'] = existing_accounts.get(rep_line.get('account_id'))

            # Template fiscal positions should not be applied, and the tax mappings cannot be determined
            tax_template.pop('fiscal_position_ids', None)
            tax_template.pop('original_tax_ids', None)

            account_xml_id = tax_template.get('cash_basis_transition_account_id')
            if account_xml_id:
                tax_template['cash_basis_transition_account_id'] = existing_accounts[account_xml_id]

        data = {
            'account.tax.group': tax_group_data,
            'account.tax': tax_data,
        }
        # prefix the xml_id with the chart template code to avoid collision
        # because since 16.2 xml_ids are regrouped under module account
        data = {
            model: {
                f"{chart_template_code}_{xml_id}": template
                for xml_id, template in templates.items()
            }
            for model, templates in data.items()
        }
        # add the prefix to the "children_tax_ids" value for group-type taxes
        for tax_data in data['account.tax'].values():
            if tax_data.get('amount_type') == 'group' and 'children_tax_ids' in tax_data:
                children_taxes = tax_data['children_tax_ids'].split(',')
                for idx, child_tax in enumerate(children_taxes):
                    children_taxes[idx] = f"{chart_template_code}_{child_tax}"
                tax_data['children_tax_ids'] = ','.join(children_taxes)
        return self._load_data(data)