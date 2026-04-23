def _get_items_from_invoices(self, excluded_move_line_ids=None, with_action=True):
        """
        Get all items from invoices, and put them into their own respective section
        (either costs or revenues)
        If the final total is 0 for either to_invoice or invoiced (ex: invoice -> credit note),
        we don't output a new section

        :param excluded_move_line_ids a list of 'account.move.line' to ignore
        when fetching the move lines, for example a list of invoices that were
        generated from a sales order
        """
        if excluded_move_line_ids is None:
            excluded_move_line_ids = []
        aml_fetch_fields = [
            'balance', 'parent_state', 'company_currency_id', 'analytic_distribution', 'move_id',
            'display_type', 'date',
        ]
        invoices_move_lines = self.env['account.move.line'].sudo().search_fetch(
            Domain.AND([
                self._get_items_from_invoices_domain([('id', 'not in', excluded_move_line_ids)]),
                [('analytic_distribution', 'in', self.account_id.ids)]
            ]),
            aml_fetch_fields,
        )
        res = {
            'revenues': {
                'data': [], 'total': {'invoiced': 0.0, 'to_invoice': 0.0}
            },
            'costs': {
                'data': [], 'total': {'billed': 0.0, 'to_bill': 0.0}
            },
        }
        # TODO: invoices_move_lines.with_context(prefetch_fields=False).move_id.move_type ??
        if invoices_move_lines:
            revenues_lines = []
            cogs_lines = []
            for move_line in invoices_move_lines:
                if move_line['display_type'] == 'cogs':
                    cogs_lines.append(move_line)
                else:
                    revenues_lines.append(move_line)
            for move_lines, ml_type in ((revenues_lines, 'revenues'), (cogs_lines, 'costs')):
                amount_invoiced = amount_to_invoice = 0.0
                for move_line in move_lines:
                    currency = move_line.company_currency_id
                    line_balance = currency._convert(move_line.balance, self.currency_id, self.company_id, move_line.date)
                    # an analytic account can appear several time in an analytic distribution with different repartition percentage
                    analytic_contribution = sum(
                        percentage for ids, percentage in move_line.analytic_distribution.items()
                        if str(self.account_id.id) in ids.split(',')
                    ) / 100.
                    if move_line.parent_state == 'draft':
                        amount_to_invoice -= line_balance * analytic_contribution
                    else:  # move_line.parent_state == 'posted'
                        amount_invoiced -= line_balance * analytic_contribution
                # don't display the section if the final values are both 0 (invoice -> credit note)
                if amount_invoiced != 0 or amount_to_invoice != 0:
                    section_id = 'other_invoice_revenues' if ml_type == 'revenues' else 'cost_of_goods_sold'
                    invoices_items = {
                        'id': section_id,
                        'sequence': self._get_profitability_sequence_per_invoice_type()[section_id],
                        'invoiced' if ml_type == 'revenues' else 'billed': amount_invoiced,
                        'to_invoice' if ml_type == 'revenues' else 'to_bill': amount_to_invoice,
                    }
                    if with_action and (
                        self.env.user.has_group('sales_team.group_sale_salesman_all_leads')
                        or self.env.user.has_group('account.group_account_invoice')
                        or self.env.user.has_group('account.group_account_readonly')
                    ):
                        invoices_items['action'] = self._get_action_for_profitability_section(invoices_move_lines.move_id.ids, section_id)
                    res[ml_type] = {
                        'data': [invoices_items],
                        'total': {
                            'invoiced' if ml_type == 'revenues' else 'billed': amount_invoiced,
                            'to_invoice' if ml_type == 'revenues' else 'to_bill': amount_to_invoice,
                        },
                    }
        return res