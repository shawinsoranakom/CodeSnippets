def _add_withholding_document_tax_total_nodes(self, line_node, vals):
        """Extends the aggregation of tax details to include Turkish (TR) withholding-specific amounts
        for an invoice line.

        This method performs the following:
            - Aggregates tax details across all base lines.
            - Adds two fields per grouping key:
                - tr_total_taxed_amount: Total tax amount used in the withholding tax line.
                - tr_total_taxed_residual_amount: Total tax amount after withholding, shown in the tax line.
            - Splits aggregated tax details into normal taxes and withholding taxes.
            - Updates `line_node` with:
                - 'cac:TaxTotal' for normal taxes
                - 'cac:WithholdingTaxTotal' for withholding taxes (if the document is an invoice)

        If there is a 20% tax and 18% is withheld on ₺10:
            - tr_total_taxed_amount = ₺2
            - tr_total_taxed_residual_amount = ₺0.2

        :param line_node: XML node representing the invoice line to be updated.
        :param vals: Dictionary containing invoice data and base lines.
        """
        base_lines_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_tax_details(vals['base_lines'], self.tax_grouping_function)
        aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(base_lines_aggregated_tax_details)

        for base_line, aggregated_values in base_lines_aggregated_tax_details:
            for grouping_key in aggregated_values:
                taxes_data = base_line.get('tax_details', {}).get('taxes_data', [])
                rounding = base_line.get('record').currency_id.rounding

                # Sum of positive tax amounts (with rounding check)
                total_taxed_amount = sum(
                    tax_line['tax_amount']
                    for tax_line in taxes_data
                    if float_compare(tax_line['tax_amount'], 0, precision_rounding=rounding) > 0
                )

                # Sum of all tax amounts
                total_residual_amount = sum(tax_line['tax_amount'] for tax_line in taxes_data)

                # Update values_per_grouping_key
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