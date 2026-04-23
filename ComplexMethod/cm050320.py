def _l10n_it_edi_grouping_function_tax_lines(self, base_line, tax_data):
        if not tax_data:
            return None
        tax = tax_data['tax']

        if tax._l10n_it_is_split_payment():
            tax_exigibility_code = 'S'
        elif tax.tax_exigibility == 'on_payment':
            tax_exigibility_code = 'D'
        elif tax.tax_exigibility == 'on_invoice':
            tax_exigibility_code = 'I'
        else:
            tax_exigibility_code = None

        return {
            'tax_amount_field': -23.0 if tax.amount in (-11.5, -4.6) else tax.amount,
            'l10n_it_exempt_reason': tax.l10n_it_exempt_reason,
            'invoice_legal_notes': html2plaintext(tax.invoice_legal_notes),
            'tax_exigibility_code': tax_exigibility_code,
            'tax_amount_type_field': tax.amount_type,
            'skip': (
                tax_data['is_reverse_charge']
                or self._l10n_it_edi_is_neg_split_payment(tax_data)
                or tax._l10n_it_filter_kind('withholding')
                or tax._l10n_it_filter_kind('pension_fund')
            ),
        }