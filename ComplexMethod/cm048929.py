def _compute_previous_order(self):
        orders_by_company = defaultdict(list)
        for order in self.filtered(lambda o: o.l10n_fr_secure_sequence_number):
            orders_by_company[order.company_id.id].append(order)

        for company_id, orders in orders_by_company.items():
            # Since sequence number can't be zero, we don't consider
            # it as a posible previous sequence number
            prev_seq = [o.l10n_fr_secure_sequence_number - 1 for o in orders if o.l10n_fr_secure_sequence_number > 1]
            prev_orders = self.search([
                ('state', 'in', ['paid', 'done']),
                ('company_id', '=', company_id),
                ('l10n_fr_secure_sequence_number', 'in', prev_seq),
            ])
            prev_map = defaultdict(list)
            for po in prev_orders:
                prev_map[po.l10n_fr_secure_sequence_number].append(po)

            for order in orders:
                match = prev_map.get(order.l10n_fr_secure_sequence_number - 1, [])
                if len(match) > 1:
                    raise UserError(_('An error occurred when computing the inalterability. Impossible to get the unique previous posted point of sale order.'))
                order.previous_order_id = match[0] if match else False