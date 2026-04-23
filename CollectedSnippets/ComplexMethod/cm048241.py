def _discountable_order(self, reward):
        """Compute the `discountable` amount (and amounts per tax group) for the current order.

        :param reward: if provided, the reward whose discountable amounts must be computed.
            It must be applicable at the order level.
        :type reward: `loyalty.reward` record, can be empty to compute the amounts regardless of the
            program configuration

        :return: A tuple with the first element being the total discountable amount of the order,
            and the second a dictionary mapping each non-fixed taxes group to its corresponding
            total untaxed amount of the eligible order lines.
        :rtype: tuple(float, dict(account.tax: float))
        """
        self.ensure_one()
        reward.ensure_one()
        assert reward.discount_applicability == 'order'

        lines = self.order_line.filtered(lambda line: not line.display_type)
        if not reward.program_id.is_payment_program:
            # Gift cards and eWallets are applied on the total order amount
            # Other types of programs are not expected to apply on delivery lines
            lines -= self._get_no_effect_on_threshold_lines()

        discountable = 0
        discountable_per_tax = defaultdict(float)

        AccountTax = self.env['account.tax']
        base_lines = []
        for line in lines:
            base_line = line._prepare_base_line_for_taxes_computation()
            taxes = base_line['tax_ids'].flatten_taxes_hierarchy()
            if not reward.program_id.is_payment_program:
                # To compute the discountable amount we get the subtotal and add
                # non-fixed tax totals. This way fixed taxes will not be discounted
                # This does not apply to Gift Cards and e-Wallet, where the total
                # order amount may be paid with the card balance
                taxes = taxes.filtered(lambda t: t.amount_type != 'fixed')
            base_line['discount_taxes'] = taxes
            base_lines.append(base_line)
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)

        def grouping_function(base_line, tax_data):
            if not tax_data:
                return None
            return {
                'taxes': base_line['discount_taxes'],
                'skip': (
                    tax_data['tax'] not in base_line['discount_taxes']
                    or base_line['record'] not in lines
                ),
            }

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            if grouping_key and grouping_key['skip']:
                continue

            taxes = grouping_key['taxes'] if grouping_key else self.env['account.tax']
            discountable += values['raw_base_amount_currency'] + values['raw_tax_amount_currency']
            discountable_per_tax[taxes] += (
                values['raw_base_amount_currency']
                + sum(
                    tax_data['raw_tax_amount_currency']
                    for base_line, taxes_data in values['base_line_x_taxes_data']
                    for tax_data in taxes_data
                    if tax_data['tax'].price_include
                )
            )
        return discountable, discountable_per_tax