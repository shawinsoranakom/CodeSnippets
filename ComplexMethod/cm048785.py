def _apply_base_lines_manual_amounts_to_reach(
        self,
        base_lines,
        company,
        target_base_amount_currency,
        target_base_amount,
        target_tax_amounts_mapping,
    ):
        """ Fix the tax amounts of the base lines passed as parameter by storing them in 'manual_tax_amounts' and make some
        adjustement to ensure the total of those lines will be exactly 'target_amount_currency'/'target_amount'.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        DEPRECATED: TO BE REMOVED IN MASTER

        :param base_lines:                  A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:                     The company owning the base lines.
        :param target_base_amount_currency: The expected base amount for the base lines expressed in foreign currency.
        :param target_base_amount:          The expected base amount for the base lines expressed in company currency.
        :param target_tax_amounts_mapping:   A mapping tax_id => dictionary containing:
            * tax_amount_currency:              The expected tax amount for the base lines expressed in foreign currency.
            * tax_amount:                       The expected tax amount for the base lines expressed in company currency.
        """
        currency = base_lines[0]['currency_id']

        # Smooth distribution of the delta base amount accross the base line, starting at the biggest one.
        sorted_base_lines = sorted(
            [
                base_line
                for base_line in base_lines
            ],
            key=lambda base_line: (bool(base_line['special_type']), -base_line['tax_details']['total_excluded_currency'])
        )
        base_lines_totals = self._compute_subset_base_lines_total(base_lines, company)
        for delta_suffix, delta_target_base_amount, delta_currency in (
            ('_currency', target_base_amount_currency, currency),
            ('', target_base_amount, company.currency_id),
        ):
            target_factors = [
                {
                    'factor': abs(
                        (base_line['tax_details']['total_excluded_currency'] + base_line['tax_details']['delta_total_excluded_currency'])
                        / base_lines_totals['base_amount_currency']
                    ),
                    'base_line': base_line,
                }
                for base_line in sorted_base_lines
            ]
            amounts_to_distribute = self._distribute_delta_amount_smoothly(
                precision_digits=delta_currency.decimal_places,
                delta_amount=delta_target_base_amount - base_lines_totals[f'base_amount{delta_suffix}'],
                target_factors=target_factors,
            )
            for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                base_line = target_factor['base_line']
                tax_details = base_line['tax_details']
                taxes_data = tax_details['taxes_data']
                if delta_suffix == '_currency':
                    base_line['price_unit'] += amount_to_distribute / abs(base_line['quantity'] or 1.0)
                if not taxes_data:
                    continue

                first_batch = taxes_data[0]['batch']
                for tax_data in taxes_data:
                    tax = tax_data['tax']
                    if tax in first_batch:
                        tax_data[f'base_amount{delta_suffix}'] += amount_to_distribute
                    else:
                        break

        for tax_id_str, tax_amounts in target_tax_amounts_mapping.items():
            for delta_suffix, delta_target_tax_amount, delta_currency in (
                ('_currency', tax_amounts['tax_amount_currency'], currency),
                ('', tax_amounts['tax_amount'], company.currency_id),
            ):
                current_tax_amounts = base_lines_totals['tax_amounts_mapping'][tax_id_str]
                if not current_tax_amounts['tax_amount_currency']:
                    continue

                target_factors = [
                    {
                        'factor': abs(tax_data['tax_amount_currency'] / current_tax_amounts['tax_amount_currency']),
                        'tax_data': tax_data,
                    }
                    for base_line in sorted_base_lines
                    for tax_data in base_line['tax_details']['taxes_data']
                    if str(tax_data['tax'].id) == tax_id_str
                ]
                amounts_to_distribute = self._distribute_delta_amount_smoothly(
                    precision_digits=delta_currency.decimal_places,
                    delta_amount=delta_target_tax_amount - current_tax_amounts[f'tax_amount{delta_suffix}'],
                    target_factors=target_factors,
                )
                for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                    tax_data = target_factor['tax_data']
                    tax_data[f'tax_amount{delta_suffix}'] += amount_to_distribute

        self._fix_base_lines_tax_details_on_manual_tax_amounts(
            base_lines=base_lines,
            company=company,
        )