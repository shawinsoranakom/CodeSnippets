def _compute_discount_allocation_needed(self):
        line2discounted_amount = {
            line: [
                (line.account_id, amount),
                (discount_allocation_account, -amount),
            ]
            for line in self.move_id.line_ids
            if line.display_type == 'product'
            and (discount_allocation_account := line.move_id._get_discount_allocation_account())
            and line.account_id != discount_allocation_account
            and (amount := line.currency_id.round(
                line.move_id.direction_sign * line.quantity * line.price_unit * line.discount / 100
            ))
        }

        distribution_totals = defaultdict(lambda: defaultdict(float))
        for line, discounted_amounts in line2discounted_amount.items():
            for account, amount in discounted_amounts:
                for analytic_account_id in line.analytic_distribution or {}:
                    distribution_totals[frozendict({
                        'move_id': line.move_id.id,
                        'account_id': account.id,
                        'currency_rate': line.currency_rate,
                    })][analytic_account_id] += amount

        for line in self:
            line.discount_allocation_dirty = True
            if line not in line2discounted_amount:
                line.discount_allocation_needed = False
                continue

            discount_allocation_needed = {}
            for account, amount in line2discounted_amount[line]:
                key = frozendict({
                    'move_id': line.move_id.id,
                    'account_id': account.id,
                    'currency_rate': line.currency_rate,
                })
                dist = distribution_totals[key]
                total = sum(dist.values()) or 1  # avoid division by zero
                discount_allocation_needed[key] = frozendict({
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': amount,
                    'analytic_distribution': {
                        account_id: 100 * value / total
                        for account_id, value in dist.items()
                    }
                })
            line.discount_allocation_needed = discount_allocation_needed