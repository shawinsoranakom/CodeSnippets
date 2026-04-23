def _prepare_tax_lines(self, base_lines, company, tax_lines=None):
        """ Prepare the tax journal items for the base lines.

        After calling '_add_tax_details_in_base_lines', the tax details is there on base lines.
        After calling '_round_base_lines_tax_details', the tax details is now rounded.
        After calling '_add_accounting_data_in_base_lines_tax_details', each tax_data in the tax details
        contains all accounting informations about the repartition lines.

        When calling this method, all 'tax_reps_data' in each 'tax_data' will be aggregated all together
        and rounded. The total tax amount will not change whatever the number of involved accounting
        grouping keys.
        The 'sign' value in base lines is very important for this method because that key decide the sign
        of the 'amount_currency'/'balance' of the base lines/tax lines to be updated/created.

        Don't forget to call '_add_tax_details_in_base_lines', '_round_base_lines_tax_details' and
        '_add_accounting_data_in_base_lines_tax_details' before calling this method.

        [!] Only added python-side.

        :param base_lines:          A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:             The company owning the base lines.
        :param tax_lines:           A optional list of base lines generated using the '_prepare_tax_line_for_taxes_computation'
                                    method. If specified, this method will indicate which tax lines must be deleted or updated instead
                                    of creating again all tax lines everytime.
        :return: The base amounts for base lines and the full diff about tax lines as a dictionary containing:
            tax_lines_to_add:       A list of values to be passed to account.move.line's create function.
            tax_lines_to_delete:    The list of tax lines to be removed.
            tax_lines_to_update:    A list of tuple <tax_line, grouping_key, amounts> where:
                tax_line                is the tax line to be updated,
                grouping_key            is the accounting grouping key matching the tax line and used to determine the tax line can be
                                        updated instead of created again,
                amounts                 is a dictionary containing the new values for 'tax_base_amount', 'amount_currency', 'balance'.
            base_lines_to_update:   A list of tuple <base_line, amounts> where:
                base_line               is the base line to be updated.
                amounts                 is a dictionary containing the new values for 'tax_tag_ids', 'amount_currency', 'balance'.
        """
        tax_lines_mapping = defaultdict(lambda: {
            'tax_base_amount': 0.0,
            'amount_currency': 0.0,
            'balance': 0.0,
        })

        base_lines_to_update = []
        for base_line in base_lines:
            sign = base_line['sign']
            tax_details = base_line['tax_details']
            base_lines_to_update.append((
                base_line,
                {
                    'tax_tag_ids': [Command.set(base_line['tax_tag_ids'].ids)],
                    'amount_currency': sign * (tax_details['total_excluded_currency'] + tax_details['delta_total_excluded_currency']),
                    'balance': sign * (tax_details['total_excluded'] + tax_details['delta_total_excluded']),
                },
            ))
            for tax_data in tax_details['taxes_data']:
                tax = tax_data['tax']
                for tax_rep_data in tax_data['tax_reps_data']:
                    grouping_key = frozendict(tax_rep_data['grouping_key'])
                    tax_line = tax_lines_mapping[grouping_key]
                    tax_line['name'] = base_line.get('manual_tax_line_name', tax.name)
                    tax_line['tax_base_amount'] += sign * tax_data['base_amount']
                    tax_line['amount_currency'] += sign * tax_rep_data['tax_amount_currency']
                    tax_line['balance'] += sign * tax_rep_data['tax_amount']

        # Remove tax lines having a zero amount.
        tax_lines_mapping = {
            frozendict({grouping_k: k[grouping_k] for grouping_k in k if not grouping_k.startswith('__')}): v
            for k, v in tax_lines_mapping.items()
            if (
                k['__keep_zero_line'] or (
                    not self.env['res.currency'].browse(k['currency_id']).is_zero(v['amount_currency'])
                    or not company.currency_id.is_zero(v['balance'])
                )
            )
        }

        # Compute 'tax_lines_to_update' / 'tax_lines_to_delete' / 'tax_lines_to_add'.
        tax_lines_to_update = []
        tax_lines_to_delete = []
        for tax_line in tax_lines or []:
            grouping_key = frozendict(self._prepare_tax_line_repartition_grouping_key(tax_line))
            if grouping_key in tax_lines_mapping and grouping_key not in tax_lines_to_update:
                amounts = tax_lines_mapping.pop(grouping_key)
                tax_lines_to_update.append((tax_line, grouping_key, amounts))
            else:
                tax_lines_to_delete.append(tax_line)
        tax_lines_to_add = [{**grouping_key, **values} for grouping_key, values in tax_lines_mapping.items()]

        return {
            'tax_lines_to_add': tax_lines_to_add,
            'tax_lines_to_delete': tax_lines_to_delete,
            'tax_lines_to_update': tax_lines_to_update,
            'base_lines_to_update': base_lines_to_update,
        }