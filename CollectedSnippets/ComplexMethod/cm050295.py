def _l10n_eg_eta_prepare_eta_invoice(self, invoice):
        AccountTax = self.env['account.tax']
        base_amls = invoice.line_ids.filtered(lambda x: x.display_type == 'product')
        base_lines = [invoice._prepare_product_base_line_for_taxes_computation(x) for x in base_amls]
        tax_amls = invoice.line_ids.filtered('tax_repartition_line_id')
        tax_lines = [invoice._prepare_tax_line_for_taxes_computation(x) for x in tax_amls]
        AccountTax._add_tax_details_in_base_lines(base_lines, invoice.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, invoice.company_id, tax_lines=tax_lines)

        # Tax amounts per line.

        def grouping_function_base_line(base_line, tax_data):
            if not tax_data:
                return None
            tax = tax_data['tax']
            code_split = tax.l10n_eg_eta_code.split('_')
            return {
                'rate': abs(tax.amount) if tax.amount_type != 'fixed' else 0,
                'tax_type': code_split[0].upper(),
                'sub_type': code_split[1].upper(),
            }

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_base_line)
        invoice_line_data, totals = self._l10n_eg_eta_prepare_invoice_lines_data(invoice, base_lines_aggregated_values)

        # Tax amounts for the whole document.

        def grouping_function_global(base_line, tax_data):
            if not tax_data:
                return None
            tax = tax_data['tax']
            code_split = tax.l10n_eg_eta_code.split('_')
            return {
                'tax_type': code_split[0].upper(),
            }

        def grouping_function_total_amount(base_line, tax_data):
            return True if tax_data else None

        base_lines_aggregated_values_total_amount = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_total_amount)
        values_per_grouping_key_total_amount = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values_total_amount)

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function_global)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)

        date_string = invoice.invoice_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        eta_invoice = {
            'issuer': self._l10n_eg_eta_prepare_address_data(invoice.journal_id.l10n_eg_branch_id, invoice, issuer=True,),
            'receiver': self._l10n_eg_eta_prepare_address_data(invoice.partner_id, invoice),
            'documentType': 'i' if invoice.move_type == 'out_invoice' else 'c' if invoice.move_type == 'out_refund' else 'd' if invoice.move_type == 'in_refund' else '',
            'documentTypeVersion': '1.0',
            'dateTimeIssued': date_string,
            'taxpayerActivityCode': invoice.journal_id.l10n_eg_activity_type_id.code,
            'internalID': invoice.name,
        }
        eta_invoice.update({
            'invoiceLines': invoice_line_data,
            'taxTotals': [
                {
                    'taxType': grouping_key['tax_type'],
                    'amount': self._l10n_eg_edi_round(abs(tax_values['tax_amount'])),
                }
                for grouping_key, tax_values in values_per_grouping_key.items()
                if grouping_key
            ],
            'totalDiscountAmount': self._l10n_eg_edi_round(totals['discount_total']),
            'totalSalesAmount': self._l10n_eg_edi_round(totals['total_price_subtotal_before_discount']),
            'netAmount': self._l10n_eg_edi_round(sum(x['base_amount'] for x in values_per_grouping_key_total_amount.values())),
            'totalAmount': self._l10n_eg_edi_round(sum(x['base_amount'] + x['tax_amount'] for x in values_per_grouping_key_total_amount.values())),
            'extraDiscountAmount': 0.0,
            'totalItemsDiscountAmount': 0.0,
        })
        if invoice.ref:
            eta_invoice['purchaseOrderReference'] = invoice.ref
        if invoice.invoice_origin:
            eta_invoice['salesOrderReference'] = invoice.invoice_origin
        return eta_invoice