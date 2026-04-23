def _import_ubl_invoice_add_base_lines(self, collected_values):
        AccountTax = self.env['account.tax']
        base_lines = collected_values['base_lines'] = []
        company = collected_values['company']
        lines_collected_values = collected_values['lines_collected_values']

        # Allowances / charges lines at document level.
        for allowance_charge in collected_values['charges'] + collected_values['allowances']:
            base_line_kwargs = self._import_ubl_invoice_get_allowance_charge_line_kwargs({
                **collected_values,
                'allowance_charge': allowance_charge,
            })
            base_lines.append(AccountTax._prepare_base_line_for_taxes_computation(
                record=None,
                **base_line_kwargs,
            ))

        for line_collected_values in lines_collected_values:
            to_write = line_collected_values['to_write']

            # Extract charges matched with a fixed tax.
            for charge in line_collected_values['charges']:
                attempt_tax_values = charge.get('attempt_tax_values')
                if not attempt_tax_values or not attempt_tax_values.get('tax'):
                    continue

                # Suppose price_unit = 19, quantity = 10, discount = 10%
                # for a total of 190 (before discount) and 171 (after discount).
                # A charge of 25 is already accounted in 190 and we retrieve a fixed tax of 50 / 10 = 5.
                # We need now to extract 25 from 190 as:
                # price_subtotal_before = 171
                # price_subtotal_after = 171 - 50 = 121
                # price_unit = 19 - 5 = 14
                # new_price_subtotal_before_discount = 140
                # discount = (1 - (121 / 140)) * 100 = 13.5714286%
                # That way, 14 * 10 * (1 - 0.135714286) = 121.
                # The fix tax is giving an amount of 50.
                # 121 + 50 = the original 171 we had at the beginning!
                price_subtotal_before = to_write['price_unit'] * to_write['quantity'] * (1.0 - to_write['discount'] / 100.0)
                price_subtotal_after = price_subtotal_before - charge['amount']
                to_write['price_unit'] -= charge['amount'] / to_write['quantity']
                new_price_subtotal_before_discount = to_write['price_unit'] * to_write['quantity']
                to_write['discount'] = (1 - (price_subtotal_after / new_price_subtotal_before_discount)) * 100.0

            # Product line.
            base_line_kwargs = self._import_ubl_invoice_line_get_product_base_line_kwargs(line_collected_values)
            base_lines.append(AccountTax._prepare_base_line_for_taxes_computation(
                record=None,
                **base_line_kwargs,
            ))

        # Cash rounding line.
        if collected_values.get('rounding_amount'):
            base_line_kwargs = self._import_ubl_invoice_get_rounding_base_line_kwargs(collected_values)
            base_lines.append(AccountTax._prepare_base_line_for_taxes_computation(
                record=None,
                **base_line_kwargs,
            ))

        AccountTax._add_tax_details_in_base_lines(base_lines, company)
        AccountTax._round_base_lines_tax_details(base_lines, company)

        # Fix 'price_unit' if some price-included taxes are involved.
        for base_line in base_lines:
            for tax_data in base_line['tax_details']['taxes_data']:
                if tax_data['tax'].price_include:
                    base_line['price_unit'] += tax_data['raw_tax_amount_currency']

        # Remove lines having a zero amount.
        collected_values['base_lines'] = [
            base_line
            for base_line in collected_values['base_lines']
            if not base_line['currency_id'].is_zero(base_line['tax_details']['total_included_currency'])
        ]