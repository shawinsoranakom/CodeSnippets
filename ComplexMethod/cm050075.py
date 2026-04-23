def _correct_invoice_tax_amount(self, tree, invoice):
        """ The tax total may have been modified for rounding purpose, if so we should use the imported tax and not
         the computed one """
        currency = invoice.currency_id
        # For each tax in our tax total, get the amount as well as the total in the xml.
        # Negative tax amounts may appear in invoices; they have to be inverted (since they are credit notes).
        document_amount_sign = self._get_import_document_amount_sign(tree)[1] or 1
        # We only search for `TaxTotal/TaxSubtotal` in the "root" element (i.e. not in `InvoiceLine` elements).
        for elem in tree.findall('./{*}TaxTotal/{*}TaxSubtotal'):
            percentage = elem.find('.//{*}TaxCategory/{*}Percent')
            if percentage is None:
                percentage = elem.find('.//{*}Percent')
            amount = elem.find('.//{*}TaxAmount')
            # When multi-currency invoices have TaxSubtotal in multiple TaxTotal nodes (e.g. JP PINT),
            # only correct using the document currency's TaxTotal to avoid overwriting with the wrong amount.
            if amount is not None and amount.get('currencyID') != currency.name:
                continue
            if (percentage is not None and percentage.text is not None) and (amount is not None and amount.text is not None):
                tax_percent = float(percentage.text)
                # Compare the result with our tax total on the invoice, and apply correction if needed.
                # First look for taxes matching the percentage in the xml.
                taxes = invoice.line_ids.tax_line_id.filtered(lambda tax: tax.amount == tax_percent)
                # If we found taxes with the correct amount, look for a tax line using it, and correct it as needed.
                if taxes:
                    tax_total = document_amount_sign * float(amount.text)
                    # Sometimes we have multiple lines for the same tax.
                    tax_lines = invoice.line_ids.filtered(lambda line: line.tax_line_id in taxes)
                    if tax_lines:
                        sign = -1 if invoice.is_inbound(include_receipts=True) else 1
                        tax_lines_total = currency.round(sign * sum(tax_lines.mapped('amount_currency')))
                        difference = currency.round(tax_total - tax_lines_total)
                        if not currency.is_zero(difference):
                            tax_lines[0].amount_currency += sign * difference