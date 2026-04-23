def _retrieve_taxes(self, record, line_values, tax_type, tax_exigibility=False):
        """
        Retrieve the taxes on the document line at import.

        In a UBL/CII xml, the Odoo "price_include" concept does not exist. Hence, first look for a price_include=False,
        if it is unsuccessful, look for a price_include=True.
        """
        # Taxes: all amounts are tax excluded, so first try to fetch price_include=False taxes,
        # if no results, try to fetch the price_include=True taxes. If results, need to adapt the price_unit.
        logs = []
        taxes = []
        for tax_node in line_values.pop('tax_nodes'):
            amount = float(tax_node.text)
            domain = [
                *self.env['account.journal']._check_company_domain(record.company_id),
                ('amount_type', '=', 'percent'),
                ('type_tax_use', '=', tax_type),
                ('amount', '=', amount),
            ]
            tax = self.env['account.tax']
            if hasattr(record, '_get_specific_tax'):
                tax = record._get_specific_tax(line_values['name'], 'percent', amount, tax_type).filtered_domain(domain)[:1]
            if tax_exigibility:
                if not tax and tax_exigibility:
                    tax = self.env['account.tax'].search(domain + [('price_include', '=', False), ('tax_exigibility', '=', tax_exigibility)], limit=1)
                if not tax and tax_exigibility:
                    tax = self.env['account.tax'].search(domain + [('price_include', '=', True), ('tax_exigibility', '=', tax_exigibility)], limit=1)
                if not tax:
                    logs.append(
                        _("Tax with matching exigibility could not be retrieved: '%(exigibility)s' for line '%(line)s'.",
                        exigibility=tax_exigibility,
                        line=line_values['name']),
                    )
            if not tax:
                tax = self.env['account.tax'].search(domain + [('price_include', '=', False)], limit=1)
            if not tax:
                tax = self.env['account.tax'].search(domain + [('price_include', '=', True)], limit=1)

            if not tax:
                logs.append(
                    _("Could not retrieve the tax: %(amount)s %% for line '%(line)s'.",
                    amount=amount,
                    line=line_values['name']),
                )
            else:
                taxes.append(tax.id)
                if tax.price_include:
                    line_values['price_unit'] *= (1 + tax.amount / 100)
        return taxes, logs