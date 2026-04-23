def _check_warehouse(self):
        """ Ensure that the warehouse is set in case of storable products """
        orders_without_wh = self.filtered(lambda order: order.state not in ('draft', 'cancel') and not order.warehouse_id)
        company_ids_with_wh = {
            company_id.id for [company_id] in self.env['stock.warehouse']._read_group(
                domain=[('company_id', 'in', orders_without_wh.company_id.ids)],
                groupby=['company_id'],
            )
        }
        other_company = set()
        for order_line in orders_without_wh.order_line:
            if order_line.product_id.type != 'consu':
                continue
            if order_line.route_ids.company_id and order_line.route_ids.company_id != order_line.company_id:
                other_company.add(order_line.route_ids.company_id.id)
                continue
            if order_line.order_id.company_id.id in company_ids_with_wh:
                raise UserError(_('You must set a warehouse on your sale order to proceed.'))
            self.env['stock.warehouse'].with_company(order_line.order_id.company_id)._warehouse_redirect_warning()
        other_company_warehouses = self.env['stock.warehouse'].search([('company_id', 'in', list(other_company))])
        if any(c not in other_company_warehouses.company_id.ids for c in other_company):
            raise UserError(_("You must have a warehouse for line using a delivery in different company."))