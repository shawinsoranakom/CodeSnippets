def _l10n_gr_edi_get_invoices_xml_vals(self):
        """
        Generates a dictionary containing the values needed for rendering ``l10n_gr_edi.mydata_invoice`` XML.
        :return: dict
        """
        xml_vals = {'invoice_values_list': []}

        for move in self.sorted(key='id'):
            details = []
            base_lines, _tax_lines = move._get_rounded_base_and_tax_lines()

            for line_no, base_line in enumerate(base_lines, start=1):
                line = base_line['record']
                vat_category = 8
                vat_exemption_category = ''
                if line.tax_ids and move.l10n_gr_edi_inv_type not in TYPES_WITH_VAT_EXEMPT:
                    tax = base_line['tax_details']['taxes_data'][0]['tax']  # here, `tax` is guaranteed to be a single `account.tax` record
                    vat_category = VALID_TAX_CATEGORY_MAP[int(tax.amount)]
                if vat_category == 7 and move.l10n_gr_edi_inv_type in TYPES_WITH_VAT_CATEGORY_8:
                    vat_category = 8
                if vat_category == 7:  # Need vat exemption category
                    vat_exemption_category = line.l10n_gr_edi_tax_exemption_category

                details.append({
                    'line_number': line_no,
                    'quantity': line.quantity if move.l10n_gr_edi_inv_type not in TYPES_WITH_FORBIDDEN_QUANTITY else '',
                    'detail_type': line.l10n_gr_edi_detail_type or '',
                    'net_value': base_line['tax_details']['raw_total_excluded'],
                    'vat_amount': sum(tax_data['tax_amount'] for tax_data in base_line['tax_details']['taxes_data']),
                    'vat_category': vat_category,
                    'vat_exemption_category': vat_exemption_category,
                    **self._l10n_gr_edi_common_base_line_details_values(base_line),
                })

            invoice_values = {
                '__move__': move,  # will not be rendered; for creating {move_id -> move_xml} mapping
                'header_series': '_'.join(move.name.split('/')[:-1]),
                'header_aa': move.name.split('/')[-1],
                'header_issue_date': move.date.isoformat(),
                'header_invoice_type': move.l10n_gr_edi_inv_type,
                'header_currency': move.currency_id.name,
                'header_correlate': move.l10n_gr_edi_correlation_id.l10n_gr_edi_mark or '',
                'details': details,
                'summary_total_net_value': move.amount_untaxed,
                'summary_total_vat_amount': move.amount_tax,
                'summary_total_withheld_amount': 0,
                'summary_total_fees_amount': 0,
                'summary_total_stamp_duty_amount': 0,
                'summary_total_other_taxes_amount': 0,
                'summary_total_deductions_amount': 0,
                'summary_total_gross_value': move.amount_total,
            }
            move._l10n_gr_edi_add_address_vals(invoice_values)
            move._l10n_gr_edi_add_payment_method_vals(invoice_values)
            self._l10n_gr_edi_add_sum_classification_vals(invoice_values)
            xml_vals['invoice_values_list'].append(invoice_values)

        return xml_vals