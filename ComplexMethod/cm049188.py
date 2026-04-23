def _prepare_withholding_lines_commands(self, base_lines, company):
        """
        Calculate the withholding tax amounts by using the provided tax base lines, and then compare the resulting values
        with the withholding line in self to determine which line should be updated, deleted or created.

        :returns A list of commands that should be used to update the withholding line field in the calling model.
        """
        AccountTax = self.env['account.tax']

        # The base lines completely ignore the withholding taxes.
        # Now, it's time to compute them.
        new_base_lines = []
        for base_line in base_lines:
            new_base_lines.append(AccountTax._prepare_base_line_for_taxes_computation(
                base_line,
                calculate_withholding_taxes=True,
                manual_tax_line_name=base_line.get('manual_tax_line_name'),
                filter_tax_function=None,
            ))

        AccountTax._add_tax_details_in_base_lines(new_base_lines, company)
        AccountTax._round_base_lines_tax_details(new_base_lines, company)

        # Map the existing withholding tax lines to their grouping key in order to know which line to update, create or delete.
        existing_withholding_line_map = self.grouped(key=lambda l: l._get_grouping_key())

        def grouping_function(base_line_data, tax_data):
            if not tax_data:
                return None
            account = company.withholding_tax_base_account_id or base_line_data['account_id']
            tax = tax_data['tax']
            # Note: keep this aligned with _get_grouping_key
            return {
                'name': base_line_data.get('manual_tax_line_name', tax.name),
                'analytic_distribution': base_line_data['analytic_distribution'],
                'account': account.id,
                'tax_id': tax_data['tax'].id,
                'skip': not tax_data['tax'].is_withholding_tax_on_payment,
                'currency_id': base_line_data['currency_id'].id,
            }

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(new_base_lines, grouping_function)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        withholding_line_commands = []
        for grouping_key, values in values_per_grouping_key.items():
            if not grouping_key or grouping_key['skip']:
                continue

            existing_line = existing_withholding_line_map.get(grouping_key)

            # If we have more than one existing line matching the grouping key, we will create a new one instead.
            if existing_line and len(existing_line) > 1:
                for line in existing_line[1:]:
                    withholding_line_commands.append(Command.delete(line.id))
                existing_line = existing_line[:1]

            if existing_line:
                # Compute the amount for existing withholding lines when the lines are updated in the view
                # We only want to recompute the tax amount
                withholding_line_commands.append(Command.update(existing_line.id, {
                    'source_base_amount_currency': values['base_amount_currency'],
                    'source_base_amount': values['base_amount'],
                    'source_tax_amount_currency': -values['tax_amount_currency'],
                    'source_tax_amount': -values['tax_amount'],
                }))
            else:
                withholding_line_commands.append(Command.create({
                    'name': grouping_key['name'],
                    'tax_id': grouping_key['tax_id'],
                    'analytic_distribution': grouping_key['analytic_distribution'],
                    'account_id': grouping_key['account'],
                    'source_base_amount_currency': values['base_amount_currency'],
                    'source_base_amount': values['base_amount'],
                    'source_tax_amount_currency': -values['tax_amount_currency'],
                    'source_tax_amount': -values['tax_amount'],
                    'source_tax_id': grouping_key['tax_id'],
                    'source_currency_id': grouping_key['currency_id'],
                }))

        keys_to_remove = existing_withholding_line_map.keys() - values_per_grouping_key.keys()
        for key in keys_to_remove:
            for line in existing_withholding_line_map[key]:
                withholding_line_commands.append(Command.delete(line.id))

        return withholding_line_commands