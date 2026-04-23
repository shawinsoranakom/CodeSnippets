def _import_fill_invoice_line_taxes(self, invoice, line_vals, tax_ids, tax_nodes, is_withheld, is_purchase):
        logs = []
        for tax_node in tax_nodes:
            tax_rate = find_xml_value('.//TaxRate', tax_node)
            if tax_rate:
                # Since the 'TaxRate' node isn't guaranteed to be a percentage, we can find out by
                # applying the tax rate on the taxable base, and if it's equal to the tax amount
                # then we can say this is a percentage, otherwise a fixed amount.
                taxable_base = find_xml_value('.//TaxableBase/TotalAmount', tax_node)
                tax_amount = find_xml_value('.//TaxAmount/TotalAmount', tax_node)
                is_fixed = False

                if taxable_base and tax_amount and invoice.currency_id.compare_amounts(float(taxable_base) * (float(tax_rate) / 100), float(tax_amount)) != 0:
                    is_fixed = True

                tax_excl = self._search_tax_for_import(invoice.company_id, float(tax_rate), is_fixed, is_withheld, is_purchase, price_included=False)

                if tax_excl:
                    tax_ids.append(tax_excl.id)
                elif tax_incl := self._search_tax_for_import(invoice.company_id, float(tax_rate), is_fixed, is_withheld, is_purchase, price_included=True):
                    tax_ids.append(tax_incl)
                    line_vals['price_unit'] *= (1.0 + float(tax_rate) / 100.0)
                else:
                    logs.append(_("Could not retrieve the tax: %(tax_rate)s %% for line '%(line)s'.", tax_rate=tax_rate, line=line_vals.get('name', "")))

        return logs