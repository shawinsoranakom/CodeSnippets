def _get_profitability_items(self, with_action=True):
        profitability_items = super()._get_profitability_items(with_action)
        if self.account_id:
            purchase_lines = self.env['purchase.order.line'].sudo().search([
                ('analytic_distribution', 'in', self.account_id.ids),
                ('state', 'in', 'purchase')
            ])
            purchase_order_line_invoice_line_ids = self._get_already_included_profitability_invoice_line_ids()
            with_action = with_action and (
                self.env.user.has_group('purchase.group_purchase_user')
                or self.env.user.has_group('account.group_account_invoice')
                or self.env.user.has_group('account.group_account_readonly')
            )
            if purchase_lines:
                amount_invoiced = amount_to_invoice = 0.0
                purchase_order_line_invoice_line_ids.extend(purchase_lines.invoice_lines.ids)
                for purchase_line in purchase_lines:
                    price_subtotal = purchase_line.currency_id._convert(purchase_line.price_subtotal, self.currency_id, self.company_id)
                    # an analytic account can appear several time in an analytic distribution with different repartition percentage
                    analytic_contribution = sum(
                        percentage for ids, percentage in purchase_line.analytic_distribution.items()
                        if str(self.account_id.id) in ids.split(',')
                    ) / 100.
                    purchase_line_amount_to_invoice = price_subtotal * analytic_contribution
                    invoice_lines = purchase_line.invoice_lines.filtered(
                        lambda l:
                        l.parent_state != 'cancel'
                        and l.analytic_distribution
                        and any(
                            str(self.account_id.id) in key.split(',')
                            for key in l.analytic_distribution
                        )
                    )
                    if invoice_lines:
                        # Calculate total invoiced amount (posted + draft, excluding refunds for unbilled calculation)
                        total_invoiced_amount = 0.0
                        for line in invoice_lines:
                            price_subtotal = line.currency_id._convert(line.price_subtotal, self.currency_id, self.company_id)
                            if not line.analytic_distribution:
                                continue
                            # an analytic account can appear several time in an analytic distribution with different repartition percentage
                            analytic_contribution = sum(
                                percentage for ids, percentage in line.analytic_distribution.items()
                                if str(self.account_id.id) in ids.split(',')
                            ) / 100.
                            cost = price_subtotal * analytic_contribution * (-1 if line.is_refund else 1)
                            # Only count non-refund invoices for unbilled calculation
                            if not line.is_refund:
                                total_invoiced_amount += cost
                            if line.parent_state == 'posted':
                                amount_invoiced -= cost
                            else:
                                amount_to_invoice -= cost
                        # Calculate the unbilled portion: PO amount - total invoiced amount (non-refunds only)
                        amount_to_invoice -= purchase_line_amount_to_invoice - total_invoiced_amount
                    else:
                        amount_to_invoice -= purchase_line_amount_to_invoice

                costs = profitability_items['costs']
                section_id = 'purchase_order'
                purchase_order_costs = {'id': section_id, 'sequence': self._get_profitability_sequence_per_invoice_type()[section_id], 'billed': amount_invoiced, 'to_bill': amount_to_invoice}
                if with_action:
                    purchase_order = purchase_lines.order_id
                    args = [section_id, [('id', 'in', purchase_order.ids)]]
                    if len(purchase_order) == 1:
                        args.append(purchase_order.id)
                    action = {'name': 'action_profitability_items', 'type': 'object', 'args': json.dumps(args)}
                    purchase_order_costs['action'] = action
                costs['data'].append(purchase_order_costs)
                costs['total']['billed'] += amount_invoiced
                costs['total']['to_bill'] += amount_to_invoice
            domain = [
                ('move_id.move_type', 'in', ['in_invoice', 'in_refund']),
                ('parent_state', 'in', ['draft', 'posted']),
                ('price_subtotal', '!=', 0),
                ('id', 'not in', purchase_order_line_invoice_line_ids),
            ]
            self._get_costs_items_from_purchase(domain, profitability_items, with_action=with_action)
        return profitability_items