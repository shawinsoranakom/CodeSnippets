def _add_consolidated_invoice_base_lines_vals(self, vals):
        AccountTax = self.env['account.tax']
        consolidated_invoice = vals['consolidated_invoice']
        consolidated_base_lines = []
        orders_per_line = next(iter(consolidated_invoice._separate_orders_in_lines(consolidated_invoice.pos_order_ids).values()))  # Only one config in a same consolidated invoice
        tax_data_fields = (
            'raw_base_amount_currency', 'raw_base_amount', 'raw_tax_amount_currency', 'raw_tax_amount',
            'base_amount_currency', 'base_amount', 'tax_amount_currency', 'tax_amount',
        )
        for index, orders in enumerate(orders_per_line):
            base_lines = []
            for order in orders:
                order_base_lines = order._prepare_tax_base_line_values()
                AccountTax._add_tax_details_in_base_lines(order_base_lines, consolidated_invoice.company_id)
                AccountTax._round_base_lines_tax_details(order_base_lines, consolidated_invoice.company_id)
                base_lines += order_base_lines

            # Aggregate the base lines into one.
            new_tax_details = {
                'raw_total_excluded_currency': 0.0,
                'total_excluded_currency': 0.0,
                'raw_total_excluded': 0.0,
                'total_excluded': 0.0,
                'raw_total_included_currency': 0.0,
                'total_included_currency': 0.0,
                'raw_total_included': 0.0,
                'total_included': 0.0,
                'delta_total_excluded_currency': 0.0,
                'delta_total_excluded': 0.0,
            }
            new_taxes_data_map = {}

            taxes = self.env['account.tax']
            for base_line in base_lines:
                tax_details = base_line['tax_details']
                sign = -1 if base_line['is_refund'] else 1
                for key in new_tax_details:
                    new_tax_details[key] += sign * tax_details[key]
                for tax_data in tax_details['taxes_data']:
                    tax = tax_data['tax']
                    taxes |= tax
                    if tax in new_taxes_data_map:
                        for key in tax_data_fields:
                            new_taxes_data_map[tax][key] += sign * tax_data[key]
                    else:
                        new_taxes_data_map[tax] = dict(tax_data)
                        for key in tax_data_fields:
                            new_taxes_data_map[tax][key] = sign * tax_data[key]

            total_amount_discounted = new_tax_details['total_excluded'] + new_tax_details['delta_total_excluded']
            total_amount_discounted_currency = new_tax_details['total_excluded_currency'] + new_tax_details['delta_total_excluded_currency']
            total_amount = total_amount_currency = 0.0
            for base_line in base_lines:
                sign = -1 if base_line["is_refund"] else 1
                discount_factor = 1 - (base_line['discount'] / 100.0)
                if discount_factor:
                    total_amount += sign * (base_line['tax_details']['raw_total_excluded'] / discount_factor)
                    total_amount_currency += sign * (base_line['tax_details']['raw_total_excluded_currency'] / discount_factor)
                else:
                    total_amount += sign * ((base_line['price_unit'] / base_line['rate']) * base_line['quantity'])
                    total_amount_currency += sign * (base_line['price_unit'] * base_line['quantity'])

            new_base_line = AccountTax._prepare_base_line_for_taxes_computation(
                {},
                tax_ids=taxes,
                price_unit=total_amount_currency,
                discount_amount=total_amount - total_amount_discounted,
                discount_amount_currency=total_amount_currency - total_amount_discounted_currency,
                quantity=1.0,
                currency_id=consolidated_invoice.currency_id,
                tax_details={
                    **new_tax_details,
                    'taxes_data': list(new_taxes_data_map.values()),
                },
                line_name=f"{orders[0].name}-{orders[-1].name}" if len(orders) > 1 else orders[0].name
            )
            consolidated_base_lines.append(new_base_line)

        vals['base_lines'] = consolidated_base_lines