def _discountable_amount(self, rewards_to_ignore):
        """Compute the `discountable` amount for the current order, ignoring the provided rewards.

        :param rewards_to_ignore: the rewards to ignore from the total amount (if they were already
            applied on the order)
        :type rewards_to_ignore: `loyalty.reward` recordset

        :return: The discountable amount
        :rtype: float
        """
        self.ensure_one()

        discountable = 0

        for line in self.order_line - self._get_no_effect_on_threshold_lines():
            if rewards_to_ignore and line.reward_id in rewards_to_ignore:
                # Ignore the existing reward line if it was already applied
                continue
            if not line.product_uom_qty or not line.price_unit:
                # Ignore lines whose amount will be 0 (bc of empty qty or 0 price)
                continue
            tax_data = line.tax_ids.compute_all(
                line.price_unit,
                currency=line.currency_id,
                quantity=line.product_uom_qty,
                product=line.product_id,
                partner=line.order_partner_id,
            )
            # To compute the discountable amount we get the subtotal and add
            # non-fixed tax totals. This way fixed taxes will not be discounted
            taxes = line.tax_ids.filtered(lambda t: t.amount_type != 'fixed')
            discountable += tax_data['total_excluded'] + sum(
                tax['amount'] for tax in tax_data['taxes'] if tax['id'] in taxes.ids
            )
        return discountable