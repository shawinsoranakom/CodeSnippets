def _l10n_tw_edi_check_tax_type_on_invoice_lines(self):
        """
        Check the tax type and special tax type on the invoice lines
        """
        self.ensure_one()
        product_lines = self.invoice_line_ids.filtered(lambda line: line.display_type == "product")
        errors = []
        # Invoice lines without tax or having multiple taxes are not allowed
        if product_lines.filtered(lambda line: not line.tax_ids or len(line.tax_ids) > 1):
            errors.append(self.env._("Invoice lines without taxes or more than one tax are not allowed."))

        if len(set(product_lines.tax_ids.mapped('price_include'))) > 1:
            errors.append(self.env._("Invoice lines with different tax include/exclude are not allowed."))

        # Create a set of tax types on invoice lines to check if there are multiple tax types or specific tax type on the invoice lines
        invoice_lines_tax_types = set(product_lines.tax_ids.mapped('l10n_tw_edi_tax_type'))

        if invoice_lines_tax_types:
            # Tax type "4" is a special tax rate, cannot be mixed with other tax types
            if "4" in invoice_lines_tax_types and len(invoice_lines_tax_types) > 1:
                errors.append(self.env._(
                    "Special tax type cannot be mixed with other tax types."
                ))

            special_tax_types_4 = set(product_lines.tax_ids.filtered(
                lambda t: t.l10n_tw_edi_tax_type == '4'
            ).mapped('l10n_tw_edi_special_tax_type'))

            if "4" in invoice_lines_tax_types and len(special_tax_types_4) > 1:
                errors.append(self.env._(
                    "Special tax type cannot be mixed with other special tax types."
                ))

            special_tax_types_3 = set(product_lines.tax_ids.filtered(
                lambda t: t.l10n_tw_edi_tax_type == '3'
            ).mapped('l10n_tw_edi_special_tax_type'))

            if "3" in invoice_lines_tax_types and len(special_tax_types_3) > 1:
                errors.append(self.env._(
                    "Duty free with special tax type cannot be mixed with duty free without special tax type or having more than one special tax type."
                ))

            if "3" in invoice_lines_tax_types and next(iter(special_tax_types_3)) == "8" and len(invoice_lines_tax_types) > 1:
                errors.append(self.env._(
                    "Duty free with special tax type cannot be mixed with other tax types."
                ))

            if {"2", "3"}.issubset(invoice_lines_tax_types):
                errors.append(self.env._(
                    "Tax type 2 (Zero tax rate) and type 3 (Duty free) cannot be used together."
                ))

            tax_type_1_rates = product_lines.tax_ids.filtered(
                lambda t: t.l10n_tw_edi_tax_type == '1'
            ).mapped('amount')

            if "1" in invoice_lines_tax_types and any(rate != 5 for rate in tax_type_1_rates):
                errors.append(self.env._(
                    "Amount for Taxable tax type must be 5%."
                ))
        else:
            errors.append(self.env._(
                "Please fill in the tax on the invoice lines and select the Ecpay tax type for taxes."
            ))
        return errors