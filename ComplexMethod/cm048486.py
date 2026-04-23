def _trigger_scheduler(self):
        """ Check for auto-triggered orderpoints and trigger them. """
        if not self or self.env['ir.config_parameter'].sudo().get_param('stock.no_auto_scheduler'):
            return

        orderpoints_by_company = defaultdict(lambda: self.env['stock.warehouse.orderpoint'])
        orderpoints_context_by_company = defaultdict(dict)
        for move in self:
            orderpoint = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', move.product_id.id),
                ('trigger', '=', 'auto'),
                ('location_id', 'parent_of', move.location_id.id),
                ('company_id', '=', move.company_id.id),
                '!', ('location_id', 'parent_of', move.location_dest_id.id),
            ], limit=1)
            if orderpoint:
                orderpoints_by_company[orderpoint.company_id] |= orderpoint
            if orderpoint and move.product_qty > orderpoint.product_min_qty and move.reference_ids:
                orderpoints_context_by_company[orderpoint.company_id].setdefault(orderpoint.id, set())
                orderpoints_context_by_company[orderpoint.company_id][orderpoint.id] |= set(move.reference_ids.ids)
        for company, orderpoints in orderpoints_by_company.items():
            orderpoints.with_context(origins=orderpoints_context_by_company[company])._procure_orderpoint_confirm(
                company_id=company, raise_user_error=False)