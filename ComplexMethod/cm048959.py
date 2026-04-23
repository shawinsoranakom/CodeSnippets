def tax_grouping_function(base_line, tax_data):
            tax = tax_data and tax_data['tax']
            myinvois_document = base_line['myinvois_document']

            if (
                not tax
                and not myinvois_document._is_consolidated_invoice()
                and not myinvois_document._is_consolidated_invoice_refund()
            ):
                return None  # Triggers UserError for missing tax on simple invoice.

            is_exempt_tax = tax and tax.l10n_my_tax_type == 'E'
            tax_exemption_reason = is_exempt_tax and (
                myinvois_document.myinvois_exemption_reason
                or tax.l10n_my_tax_exemption_reason
            )

            return {
                'tax_category_code': tax.l10n_my_tax_type if tax else '06',
                'tax_exemption_reason': tax_exemption_reason,
                'amount': tax.amount if tax else 0.0,
                'amount_type': tax.amount_type if tax else 'percent',
            }