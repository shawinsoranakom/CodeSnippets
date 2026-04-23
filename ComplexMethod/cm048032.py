def tax_grouping_function(_base_line, tax_data):
            tax = tax_data and tax_data['tax']
            # Exclude fixed taxes if 'fixed_taxes_as_allowance_charges' is True
            if vals['fixed_taxes_as_allowance_charges'] and tax and tax.amount_type == 'fixed':
                return None

            return {
                'tax_category_code': tax.l10n_my_tax_type if tax else '06',
                'tax_exemption_reason': tax.l10n_my_tax_exemption_reason if tax and tax.l10n_my_tax_type == 'E' else None,
                'amount': tax.amount if tax else 0.0,
                'amount_type': tax.amount_type if tax else 'percent',
            }