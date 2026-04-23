def _get_costs_items_from_purchase(self, domain, profitability_items, with_action=True):
        """ This method is used in sale_project and project_purchase. Since project_account is the only common module (except project), we create the method here. """
        # calculate the cost of bills without a purchase order
        account_move_lines = self.env['account.move.line'].sudo().search_fetch(
            domain + [('analytic_distribution', 'in', self.account_id.ids)],
            ['balance', 'parent_state', 'company_currency_id', 'analytic_distribution', 'move_id', 'date'],
        )
        if account_move_lines:
            # Get conversion rate from currencies to currency of the current company
            amount_invoiced = amount_to_invoice = 0.0
            for move_line in account_move_lines:
                line_balance = move_line.company_currency_id._convert(
                    from_amount=move_line.balance, to_currency=self.currency_id, date=move_line.date
                )
                # an analytic account can appear several time in an analytic distribution with different repartition percentage
                analytic_contribution = sum(
                    percentage for ids, percentage in move_line.analytic_distribution.items()
                    if str(self.account_id.id) in ids.split(',')
                ) / 100.
                if move_line.parent_state == 'draft':
                    amount_to_invoice -= line_balance * analytic_contribution
                else:  # move_line.parent_state == 'posted'
                    amount_invoiced -= line_balance * analytic_contribution
            # don't display the section if the final values are both 0 (bill -> vendor credit)
            if amount_invoiced != 0 or amount_to_invoice != 0:
                costs = profitability_items['costs']
                section_id = 'other_purchase_costs'
                bills_costs = {
                    'id': section_id,
                    'sequence': self._get_profitability_sequence_per_invoice_type()[section_id],
                    'billed': amount_invoiced,
                    'to_bill': amount_to_invoice,
                }
                if with_action:
                    bills_costs['action'] = self._get_action_for_profitability_section(account_move_lines.move_id.ids, section_id)
                costs['data'].append(bills_costs)
                costs['total']['billed'] += amount_invoiced
                costs['total']['to_bill'] += amount_to_invoice