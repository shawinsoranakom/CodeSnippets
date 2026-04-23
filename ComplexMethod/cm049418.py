def _add_withholding_document_line_tax_total_nodes(self, line_node, vals):
        """Extend aggregation of line tax details to include Turkish (TR) withholding-specific amounts.

        For each tax grouping key, this method adds two fields:
            - tr_total_taxed_amount: The total tax amount applied to the line before withholding.
            - tr_total_taxed_residual_amount: The remaining tax amount after withholding.

        If there is a 20% tax and 18% is withheld on ₺10:
            - tr_total_taxed_amount = ₺2
            - tr_total_taxed_residual_amount = ₺0.2

        :param line_node: The invoice line node containing tax details.
        :param vals: Tax values used to compute withholding amounts.
        """
        encountered_groups = set()
        base_line = vals['base_line']
        tax_details = base_line['tax_details']
        taxes_data = tax_details['taxes_data']
        aggregated_tax_details = self.env['account.tax']._aggregate_base_line_tax_details(base_line, self.tax_grouping_function)

        for tax_data in taxes_data:
            grouping_key = self.tax_grouping_function(base_line, tax_data)
            if isinstance(grouping_key, dict):
                grouping_key = frozendict(grouping_key)
            already_accounted = grouping_key in encountered_groups
            encountered_groups.add(grouping_key)
            if not already_accounted:
                taxes_data = base_line.get('tax_details', {}).get('taxes_data', [])
                rounding = base_line.get('record').currency_id.rounding

                total_taxed_amount = sum(tax_line['tax_amount'] for tax_line in taxes_data if float_compare(tax_line['tax_amount'], 0, precision_rounding=rounding) > 0)
                total_residual_amount = sum(tax_line['tax_amount'] for tax_line in taxes_data)

                group_vals = aggregated_tax_details[grouping_key]
                group_vals['tr_total_taxed_amount'] = group_vals.get('tr_total_taxed_amount', 0.0) + total_taxed_amount
                group_vals['tr_total_taxed_residual_amount'] = group_vals.get('tr_total_taxed_residual_amount', 0.0) + total_residual_amount

        aggregated_tax_details_by_l10n_tr_tax_withholding_code_id = {'tax': defaultdict(dict), 'withholding_tax': defaultdict(dict)}

        for grouping_key, values in aggregated_tax_details.items():
            if grouping_key:
                key = 'withholding_tax' if (l10n_tr_tax_withheld := grouping_key['l10n_tr_tax_withheld']) else 'tax'
                aggregated_tax_details_by_l10n_tr_tax_withholding_code_id[key][l10n_tr_tax_withheld][grouping_key] = values

        line_node['cac:TaxTotal'] = [
            self._get_withholding_tax_total_node({**vals, 'aggregated_tax_details': tax_details, 'role': 'line'})
            for tax_details in aggregated_tax_details_by_l10n_tr_tax_withholding_code_id['tax'].values()
        ]
        if vals['document_type'] == 'invoice':
            line_node['cac:WithholdingTaxTotal'] = [
                self._get_withholding_tax_total_node({**vals, 'aggregated_tax_details': tax_details, 'role': 'line', 'withholding': True, 'sign': -1})
                for tax_details in aggregated_tax_details_by_l10n_tr_tax_withholding_code_id['withholding_tax'].values()
            ]