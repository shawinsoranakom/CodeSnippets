def _get_line_vals(self, productions=False, date=False):
        if not productions:
            productions = self.env['mrp.production']
        if not date:
            date = datetime.now().replace(hour=23, minute=59, second=59)
        compo_value = sum(
            ml.quantity_product_uom * (ml.product_id.lot_valuated and ml.lot_id and ml.lot_id.standard_price or ml.product_id.standard_price)
            for ml in productions.move_raw_ids.move_line_ids.filtered(lambda ml: ml.picked and ml.quantity and ml.date <= date)
        )
        overhead_value = productions.workorder_ids._cal_cost(date)
        sval_acc = self.env['product.category']._fields['property_stock_valuation_account_id'].get_company_dependent_fallback(self.env['product.category']).id
        return [
            Command.create({
                'label': _("WIP - Component Value"),
                'credit': compo_value,
                'account_id': sval_acc,
            }),
            Command.create({
                'label': _("WIP - Overhead"),
                'credit': overhead_value,
                'account_id': self._get_overhead_account(),
            }),
            Command.create({
                'label': _("Manufacturing WIP - %(orders_list)s", orders_list=productions.mapped('name') or _("Manual Entry")),
                'debit': compo_value + overhead_value,
                'account_id': self.env.company.account_production_wip_account_id.id,
            })
        ]