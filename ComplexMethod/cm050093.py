def _import_ubl_invoice_add_tax_total_values(self, collected_values):
        file_document_sign = collected_values['file_document_sign']
        odoo_document_type = collected_values['odoo_document_type']
        currency = collected_values['currency_values']['currency']

        taxes_values = collected_values['tax_total_values'] = {}
        tree = collected_values['tree']
        for subtotal_elem in tree.findall('./{*}TaxTotal/{*}TaxSubtotal'):
            amount_node = subtotal_elem.find('.//{*}TaxAmount')
            category_code = subtotal_elem.findtext('.//{*}TaxCategory/{*}ID')
            if amount_node is None or category_code is None:
                continue

            amount = amount_node.text

            if amount_node.get('currencyID') and amount_node.get('currencyID') != currency.name:
                continue

            percentage = subtotal_elem.findtext('.//{*}TaxCategory/{*}Percent')
            if percentage is None:
                percentage = subtotal_elem.find('.//{*}Percent')
            if percentage is None:
                continue

            percentage = float(percentage)
            tax_key = frozendict({
                'category_code': category_code,
                'percentage': percentage,
            })
            tax_values = taxes_values.setdefault(tax_key, {
                'amount_type': 'percent',
                'type_tax_use': odoo_document_type,
                'amount': percentage,
                'ubl_cii_tax_category_code': category_code,
                'tax_amount_currency': 0.0,
                'related_taxes_values': [],
            })
            tax_values['tax_amount_currency'] += file_document_sign * float(amount)