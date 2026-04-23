def _prepare_withholding_amls_create_values(self):
        """ Prepare and return a list of values that will be used to create the journal items for the withholding lines.

        For an invoice for 1000 with 10% withholding tax:
        Outstanding:              900.0
        Receivable:               -1000.0
        Tax withheld:             100.0
        WHT base:                 1000.0
        WHT base counterpart:     1000.0

        :return: A list of dictionaries, each one being a journal item to be created.
        """
        if not self:
            return []

        company = self.company_id
        AccountTax = self.env['account.tax']

        # Check names first to not consume sequences if any is missing
        for line in self:
            if not line.name and not line.withholding_sequence_id:
                raise UserError(self.env._('Please enter the withholding number for the tax %(tax_name)s', tax_name=line.tax_id.name))

        # Convert them to base lines to compute the taxes.
        base_lines = []
        for line in self:
            if not line.name:
                line.name = line.tax_id.withholding_sequence_id.next_by_id()

            base_line = line._prepare_base_line_for_taxes_computation()
            AccountTax._add_tax_details_in_base_line(base_line, company)
            base_lines.append(base_line)
        AccountTax._round_base_lines_tax_details(base_lines, company)
        AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, company)
        tax_results = AccountTax._prepare_tax_lines(base_lines, company)

        # Add the tax lines.
        aml_create_values_list = []
        for tax_line_vals in tax_results['tax_lines_to_add']:
            aml_create_values_list.append({
                **tax_line_vals,
                'name': self.env._("WH Tax: %(name)s", name=tax_line_vals['name']),
                'amount_currency': -tax_line_vals['amount_currency'],
                'balance': -tax_line_vals['balance'],
                'partner_id': self._get_comodel_partner().id,
            })

        # Aggregate the base lines.
        aggregated_base_lines = defaultdict(lambda: {
            'names': set(),
            'amount_currency': 0.0,
            'balance': 0.0,
        })
        for base_line, to_update in tax_results['base_lines_to_update']:
            grouping_key = frozendict({
                **AccountTax._prepare_base_line_grouping_key(base_line),
                'tax_tag_ids': to_update['tax_tag_ids'],
            })
            aggregated_amounts = aggregated_base_lines[grouping_key]
            aggregated_amounts['names'].add(base_line['record'].name)
            aggregated_amounts['amount_currency'] += to_update['amount_currency']
            aggregated_amounts['balance'] += to_update['balance']

        # Add the base lines.
        for grouping_key, amounts in aggregated_base_lines.items():
            aml_create_values_list.append({
                **grouping_key,
                'name': self.env._('WH Base: %(names)s', names=', '.join(amounts['names'])),
                'tax_ids': [],
                'tax_tag_ids': [],
                'amount_currency': amounts['amount_currency'],
                'balance': amounts['balance'],
                'partner_id': self._get_comodel_partner().id,
            })
            aml_create_values_list.append({
                **grouping_key,
                'name': self.env._('WH Base Counterpart: %(names)s', names=', '.join(amounts['names'])),
                'analytic_distribution': None,
                'amount_currency': -amounts['amount_currency'],
                'balance': -amounts['balance'],
                'partner_id': self._get_comodel_partner().id,
            })

        return aml_create_values_list