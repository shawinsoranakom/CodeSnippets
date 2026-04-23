def _post_labour(self):
        for mo in self:
            production_location = self.product_id.with_company(self.company_id).property_stock_production
            if mo.with_company(mo.company_id).product_id.valuation != 'real_time' or not production_location.valuation_account_id:
                continue

            if mo.workorder_ids.time_ids.account_move_line_id:
                continue

            product_accounts = mo.product_id.product_tmpl_id.get_product_accounts()
            labour_amounts = defaultdict(float)
            workorders = defaultdict(self.env['mrp.workorder'].browse)
            for wo in mo.workorder_ids:
                account = wo.workcenter_id.expense_account_id or product_accounts['expense']
                labour_amounts[account] += wo.company_id.currency_id.round(wo._cal_cost())
                workorders[account] |= wo
            workcenter_cost = sum(labour_amounts.values())

            if mo.company_id.currency_id.is_zero(workcenter_cost):
                continue

            desc = _('%s - Labour', mo.name)
            account = production_location.valuation_account_id
            labour_amounts[account] -= workcenter_cost
            account_move = self.env['account.move'].sudo().create({
                'journal_id': product_accounts['stock_journal'].id,
                'date': fields.Date.context_today(self),
                'ref': desc,
                'move_type': 'entry',
                'line_ids': [(0, 0, {
                    'name': desc,
                    'ref': desc,
                    'balance': -amt,
                    'account_id': acc.id,
                }) for acc, amt in labour_amounts.items()]
            })
            account_move._post()
            for line in account_move.line_ids[:-1]:
                workorders[line.account_id].time_ids.write({'account_move_line_id': line.id})