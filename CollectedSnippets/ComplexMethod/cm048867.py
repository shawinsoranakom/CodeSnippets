def _get_replenishment_multiple_alternative(self, qty_to_order):
        self.ensure_one()
        routes = self.effective_route_id or self.product_id.route_ids
        if not (self.product_id and any(r.action == 'buy' for r in routes.rule_ids)):
            return super()._get_replenishment_multiple_alternative(qty_to_order)
        planned_date = self._get_orderpoint_procurement_date()
        global_horizon_days = self.get_horizon_days()
        if global_horizon_days:
            planned_date -= relativedelta.relativedelta(days=int(global_horizon_days))
        date_deadline = planned_date or fields.Date.today()
        dates_info = self.product_id._get_dates_info(date_deadline, self.location_id, route_ids=self.route_id)
        supplier = self.supplier_id or self.product_id.with_company(self.company_id)._select_seller(
            quantity=qty_to_order,
            date=max(dates_info['date_order'].date(), fields.Date.today()),
            uom_id=self.product_uom
        )
        return supplier.product_uom_id