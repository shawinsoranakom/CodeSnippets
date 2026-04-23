def _add_base_lines_tax_amounts(self, base_lines, company, tax_lines=None):
        AccountTax = self.env['account.tax']
        AccountTax._add_tax_details_in_base_lines(base_lines, company)
        AccountTax._round_base_lines_tax_details(base_lines, company, tax_lines=tax_lines)

        for base_line in base_lines:
            discount = base_line['discount']
            price_unit = base_line['price_unit'] / base_line['rate'] if base_line['rate'] else 0.0
            quantity = base_line['quantity']
            price_subtotal = base_line['price_subtotal'] = base_line['tax_details']['raw_total_excluded']
            base_line['price_total'] = base_line['tax_details']['raw_total_included']
            for tax_data in base_line['tax_details']['taxes_data']:
                if tax_data['tax'].l10n_es_type == 'retencion':
                    base_line['price_total'] -= tax_data['tax_amount']

            if discount == 100.0:
                gross_price_subtotal_before_discount = price_unit * quantity
            else:
                gross_price_subtotal_before_discount = price_subtotal / (1 - discount / 100.0)

            base_line['gross_price_subtotal'] = gross_price_subtotal_before_discount
            base_line['discount_amount'] = gross_price_subtotal_before_discount - price_subtotal
            base_line['description'] = re.sub(r'[^0-9a-zA-Z ]+', '', base_line['name'] or base_line['product_id'].display_name or '')[:250]

            if quantity:
                base_line['gross_price_unit'] = gross_price_subtotal_before_discount / quantity
            else:
                base_line['gross_price_unit'] = 0.0