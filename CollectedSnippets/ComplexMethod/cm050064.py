def _ubl_get_tax_subtotal_node(self, vals, tax_subtotal):
        # EXTENDS account.edi.xml.ubl
        node = super()._ubl_get_tax_subtotal_node(vals, tax_subtotal)

        # [BR-S-08]/[BR-E-08]/[BR-Z-08]/... cac:TaxSubtotal -> cbc:TaxableAmount should be
        # computed based on the cbc:LineExtensionAmount of each line linked to the tax.
        # This applies to all tax category codes (S, E, Z, AE, etc.) as each has a
        # corresponding BR-*-08 schematron rule requiring this consistency.
        currency = tax_subtotal['currency']
        corresponding_line_node_amounts = [
            line_node['cbc:LineExtensionAmount']['_text']
            for tax_category_node in node['cac:TaxCategory']
            for line_key in ('cac:InvoiceLine', 'cac:CreditNoteLine', 'cac:DebitNoteLine')
            for line_node in vals['document_node'].get(line_key, [])
            for line_node_tax_category_node in line_node['cac:Item']['cac:ClassifiedTaxCategory']
            if (
                line_node_tax_category_node['cbc:ID']['_text'] == tax_category_node['cbc:ID']['_text']
                and line_node_tax_category_node['cbc:Percent']['_text'] == tax_category_node['cbc:Percent']['_text']
                and line_node_tax_category_node['_currency'] == tax_category_node['_currency']
            )
        ] + [
            -allowance_node['cbc:Amount']['_text']
            for tax_category_node in node['cac:TaxCategory']
            for allowance_node in vals['document_node']['cac:AllowanceCharge']
            if allowance_node['cbc:ChargeIndicator']['_text'] == 'false'
            for allowance_node_tax_category_node in allowance_node['cac:TaxCategory']
            if (
                allowance_node_tax_category_node['cbc:ID']['_text'] == tax_category_node['cbc:ID']['_text']
                and allowance_node_tax_category_node['cbc:Percent']['_text'] == tax_category_node['cbc:Percent']['_text']
                and allowance_node_tax_category_node['_currency'] == tax_category_node['_currency']
            )
        ] + [
            allowance_node['cbc:Amount']['_text']
            for tax_category_node in node['cac:TaxCategory']
            for allowance_node in vals['document_node']['cac:AllowanceCharge']
            if allowance_node['cbc:ChargeIndicator']['_text'] == 'true'
            for allowance_node_tax_category_node in allowance_node['cac:TaxCategory']
            if (
                allowance_node_tax_category_node['cbc:ID']['_text'] == tax_category_node['cbc:ID']['_text']
                and allowance_node_tax_category_node['cbc:Percent']['_text'] == tax_category_node['cbc:Percent']['_text']
                and allowance_node_tax_category_node['_currency'] == tax_category_node['_currency']
            )
        ]
        if corresponding_line_node_amounts:
            node['cbc:TaxableAmount'] = {
                '_text': FloatFmt(sum(corresponding_line_node_amounts), max_dp=currency.decimal_places),
                'currencyID': currency.name,
            }

        # Percent is not reported in TaxSubtotal
        node['cbc:Percent']['_text'] = None

        return node