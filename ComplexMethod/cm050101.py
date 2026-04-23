def _import_ubl_invoice_fix_taxes_amounts(self, collected_values):
        AccountTax = self.env['account.tax']
        invoice = collected_values['invoice']
        tax_total_values = collected_values['tax_total_values']
        tolerance = 0.03
        total_tax_amount = sum(x['tax_amount_currency'] for x in tax_total_values.values())
        currency = collected_values['currency_values']['currency']

        tax_to_taxes = {}
        taxes_to_tax_amount_currency = {}
        is_complete = True
        for tax_key, global_tax_values in tax_total_values.items():
            taxes = self.env['account.tax']
            for related_tax_values in global_tax_values['related_taxes_values']:
                tax = related_tax_values.get('tax')
                if tax:
                    taxes |= tax
                else:
                    is_complete = False
                    break

            for tax in taxes:
                tax_to_taxes[tax] = taxes
            taxes_to_tax_amount_currency[taxes] = global_tax_values['tax_amount_currency']

        # If we are too far away from the total retrieved in the xml, don't fix anything: the error is elsewhere.
        if (
            not is_complete
            or currency.compare_amounts(abs(invoice.amount_tax - total_tax_amount) - tolerance, 0.0) > 0
        ):
            return

        # Fix the base lines.
        def grouping_function(_base_line, tax_data):
            return tax_data and tax_to_taxes.get(tax_data['tax'])

        base_lines, tax_lines = invoice._get_rounded_base_and_tax_lines()
        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for taxes, values in values_per_grouping_key.items():
            if not taxes:
                continue

            target_tax_amount_currency = taxes_to_tax_amount_currency[taxes]
            target_factors = [
                {
                    'factor': tax_data['raw_tax_amount_currency'],
                    'tax_data': tax_data,
                }
                for _base_line, taxes_data in values['base_line_x_taxes_data']
                for tax_data in taxes_data
            ]
            amounts_to_distribute = AccountTax._distribute_delta_amount_smoothly(
                precision_digits=currency.decimal_places,
                delta_amount=target_tax_amount_currency,
                target_factors=target_factors,
            )
            for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                tax_data = target_factor['tax_data']
                tax_data['tax_amount_currency'] = amount_to_distribute

        AccountTax._add_accounting_data_in_base_lines_tax_details(base_lines, invoice.company_id, include_caba_tags=invoice.always_tax_exigible)
        tax_results = AccountTax._prepare_tax_lines(base_lines, invoice.company_id, tax_lines=tax_lines)

        line_ids_commands = []
        for tax_line_vals, grouping_key, to_update in tax_results['tax_lines_to_update']:
            line_ids_commands.append(Command.update(tax_line_vals['record'].id, {
                'amount_currency': to_update['amount_currency'],
                'balance': to_update['balance'],
            }))

        container = {'records': invoice}
        with (
            invoice._check_balanced(container),
            invoice._disable_discount_precision(),
            invoice._sync_dynamic_lines(container),
        ):
            invoice.line_ids = line_ids_commands