def _import_document_allowance_charges(self, tree, record, tax_type, qty_factor=1):
        logs = []
        xpaths = self._get_document_allowance_charge_xpaths()
        line_vals = []
        for allow_el in tree.iterfind(xpaths['root']):
            name = allow_el.findtext(xpaths['reason']) or ""
            # Charge indicator factor: -1 for discount, 1 for charge
            charge_indicator = -1 if allow_el.findtext(xpaths['charge_indicator']).lower() == 'false' else 1
            amount = float(allow_el.findtext(xpaths['amount']) or 0)
            base_amount = float(allow_el.findtext(xpaths['base_amount']) or 0)
            if base_amount:
                price_unit = base_amount * charge_indicator * qty_factor
                percentage = float(allow_el.findtext(xpaths['percentage']) or 100)
                quantity = percentage / 100
            else:
                price_unit = amount * charge_indicator * qty_factor
                quantity = 1

            # Taxes
            tax_ids = []
            for tax_percent_node in allow_el.iterfind(xpaths['tax_percentage']):
                tax_amount = float(tax_percent_node.text)
                tax = self.env['account.tax'].search([
                    *self.env['account.tax']._check_company_domain(record.company_id),
                    ('amount', '=', tax_amount),
                    ('amount_type', '=', 'percent'),
                    ('type_tax_use', '=', tax_type),
                ], limit=1)
                if tax:
                    tax_ids += tax.ids
                elif name:
                    logs.append(_(
                        "Could not retrieve the tax: %(tax_percentage)s %% for line '%(line)s'.",
                        tax_percentage=tax_amount,
                        line=name,
                    ))
                else:
                    logs.append(
                        _("Could not retrieve the tax: %s for the document level allowance/charge.", tax_amount))

            line_vals.append([name, quantity, price_unit, tax_ids])
        return record._get_line_vals_list(line_vals), logs