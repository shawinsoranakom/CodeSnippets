def _ubl_add_tax_totals_nodes(self, vals):
        AccountTax = self.env['account.tax']
        base_lines = vals['base_lines']
        company = vals['company']
        company_currency = company.currency_id
        currency = vals['currency_id']

        iter_currency = [(currency, '_currency')]
        if currency != company_currency:
            iter_currency.append((company_currency, ''))

        # Since we have to combine 3 keys given by the same grouping key but used at 3 different places, we compute them in advance.
        # /!\ Even without tax, a base line could get a grouping key for a 0% tax without any real record set.
        new_base_lines = [
            {
                **base_line,
                '_tax_totals_keys': {
                    (tax_data['tax'] if tax_data else None, currency): self._ubl_tax_totals_node_grouping_key(base_line, tax_data, vals, currency)
                    for currency, _suffix in iter_currency
                    for tax_data in base_line['tax_details']['taxes_data'] or [None]
                }
            }
            for base_line in base_lines
        ]

        collected_tax_totals_values = {
            'cac:TaxTotal': {},
            'cac:WithholdingTaxTotal': {},
        }
        for sub_currency, suffix in iter_currency:

            # tax_totals / withholding_tax_totals

            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(
                base_lines=new_base_lines,
                grouping_function=lambda base_line, tax_data: base_line['_tax_totals_keys'][(tax_data or {}).get('tax'), sub_currency]['tax_total_key']
            )
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue

                if grouping_key['is_withholding']:
                    target_key = 'cac:WithholdingTaxTotal'
                    sign = -1
                else:
                    target_key = 'cac:TaxTotal'
                    sign = 1

                collected_tax_totals_values[target_key][frozendict(grouping_key)] = {
                    **grouping_key,
                    'amount': sign * values[f'tax_amount{suffix}'],
                    'subtotals': {},
                }

            # tax_subtotals

            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(
                base_lines=new_base_lines,
                grouping_function=lambda base_line, tax_data: {
                    k: v
                    for k, v in base_line['_tax_totals_keys'][(tax_data or {}).get('tax'), sub_currency].items()
                    if k in ('tax_total_key', 'tax_subtotal_key')
                },
            )
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue
                tax_total_key = grouping_key['tax_total_key']
                tax_subtotal_key = grouping_key['tax_subtotal_key']
                if not tax_total_key or not tax_subtotal_key:
                    continue

                if tax_total_key['is_withholding']:
                    target_key = 'cac:WithholdingTaxTotal'
                    sign = -1
                else:
                    target_key = 'cac:TaxTotal'
                    sign = 1

                tax_total_values = collected_tax_totals_values[target_key][frozendict(tax_total_key)]
                tax_total_values['subtotals'][frozendict(tax_subtotal_key)] = {
                    **tax_subtotal_key,
                    'base_amount': values[f'base_amount{suffix}'],
                    'tax_amount': sign * values[f'tax_amount{suffix}'],
                    'tax_categories': {},
                }

            # tax_categories

            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(
                base_lines=new_base_lines,
                grouping_function=lambda base_line, tax_data: base_line['_tax_totals_keys'][(tax_data or {}).get('tax'), sub_currency],
            )
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue
                tax_total_key = grouping_key['tax_total_key']
                tax_subtotal_key = grouping_key['tax_subtotal_key']
                tax_category_key = grouping_key['tax_category_key']
                if not tax_total_key or not tax_subtotal_key or not tax_category_key:
                    continue

                if tax_total_key['is_withholding']:
                    target_key = 'cac:WithholdingTaxTotal'
                    sign = -1
                else:
                    target_key = 'cac:TaxTotal'
                    sign = 1

                tax_total_values = collected_tax_totals_values[target_key][frozendict(tax_total_key)]
                tax_subtotal_values = tax_total_values['subtotals'][frozendict(tax_subtotal_key)]
                tax_subtotal_values['tax_categories'][frozendict(tax_category_key)] = {
                    **tax_category_key,
                    'base_amount': values[f'base_amount{suffix}'],
                    'tax_amount': sign * values[f'tax_amount{suffix}'],
                }

        for key, tax_totals_values in collected_tax_totals_values.items():
            nodes = vals['document_node'][key] = []
            for tax_total_values in tax_totals_values.values():
                tax_total_node = self._ubl_get_tax_total_node(vals, tax_total_values)
                nodes.append(tax_total_node)