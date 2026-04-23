def _compute_epd_needed(self):
        AccountTax = self.env['account.tax']
        self.epd_dirty = True
        self.epd_needed = False

        candidate_invoice_lines = self.filtered(lambda l: (
            l.move_id.invoice_payment_term_id.early_discount
            and l.display_type == 'product'
            and l.tax_ids
            and l.move_id.invoice_payment_term_id.early_pay_discount_computation == 'mixed'
        ))

        def grouping_function(base_line, tax_data):
            return {
                'account_id': base_line['account_id'].id,
                'analytic_distribution': base_line['analytic_distribution'],
                'tax_ids': [Command.set([tax_data['tax'].id for tax_data in base_line['tax_details']['taxes_data']])],
            }

        def dispatch_exclude_function(base_line, tax_data):
            return not tax_data['tax']._can_be_discounted()

        result_per_invoice_line = {}
        for move in candidate_invoice_lines.move_id:
            company = move.company_id or self.env.company
            currency = move.currency_id or company.currency_id
            discount_percentage = move.invoice_payment_term_id.discount_percentage
            discount_percentage_name = f"{discount_percentage}%"
            percentage = discount_percentage / 100
            sign = move.direction_sign

            # Get the amounts for each invoice line.
            invoice_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
            base_lines = [
                {
                    **move._prepare_product_base_line_for_taxes_computation(line),
                    '_invoice_line': line,
                }
                for line in invoice_lines
            ]
            AccountTax._add_tax_details_in_base_lines(base_lines, company)
            AccountTax._round_base_lines_tax_details(base_lines, company)

            # store the invoice line record
            for base_line in base_lines:
                base_line['_invoice_line'] = base_line['record']

            # Fixed taxes have to be excluded.
            base_lines = AccountTax._dispatch_taxes_into_new_base_lines(base_lines, company, dispatch_exclude_function)

            # Compute the total untaxed amount.
            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function)
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue

                # Compute the early payment discount total.
                epd_amount_currency = currency.round(sign * values['total_excluded_currency'] * percentage)
                epd_balance = company.currency_id.round(sign * values['total_excluded'] * percentage)

                # Distribute it on aggregated base_lines.
                grouping_key_line = frozendict({
                    'move_id': move.id,
                    **grouping_key,
                    'display_type': 'epd',
                })
                grouping_key_counterpart = frozendict({
                    'move_id': move.id,
                    'account_id': grouping_key['account_id'],
                    'display_type': 'epd',
                })
                aggregated_base_lines = [
                    base_line
                    for base_line, _taxes_data in values['base_line_x_taxes_data']
                ]
                for base_line in aggregated_base_lines:
                    invoice_line = base_line['_invoice_line']
                    result_per_invoice_line[invoice_line] = {
                        grouping_key_line: {
                            'name': _("Early Payment Discount (%s)", discount_percentage_name),
                            'amount_currency': 0.0,
                            'balance': 0.0,
                        },
                        grouping_key_counterpart: {
                            'name': _("Early Payment Discount (%s)", discount_percentage_name),
                            'amount_currency': 0.0,
                            'balance': 0.0,
                            'tax_ids': [Command.clear()],
                        },
                    }

                target_factors = [
                    {
                        'factor': base_line['tax_details']['raw_total_excluded_currency'],
                        'base_line': base_line,
                    }
                    for base_line in aggregated_base_lines
                ]
                amounts_to_distribute = AccountTax._distribute_delta_amount_smoothly(
                    precision_digits=currency.decimal_places,
                    delta_amount=epd_amount_currency,
                    target_factors=target_factors,
                )
                for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                    invoice_line = target_factor['base_line']['_invoice_line']
                    epd_needed = result_per_invoice_line[invoice_line]
                    epd_needed[grouping_key_line]['amount_currency'] -= amount_to_distribute
                    epd_needed[grouping_key_counterpart]['amount_currency'] += amount_to_distribute

                amounts_to_distribute = AccountTax._distribute_delta_amount_smoothly(
                    precision_digits=company.currency_id.decimal_places,
                    delta_amount=epd_balance,
                    target_factors=target_factors,
                )
                for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                    invoice_line = target_factor['base_line']['_invoice_line']
                    epd_needed = result_per_invoice_line[invoice_line]
                    epd_needed[grouping_key_line]['balance'] -= amount_to_distribute
                    epd_needed[grouping_key_counterpart]['balance'] += amount_to_distribute

        for invoice_line in candidate_invoice_lines:
            epd_needed = result_per_invoice_line[invoice_line]
            invoice_line.epd_needed = {k: frozendict(v) for k, v in epd_needed.items()}