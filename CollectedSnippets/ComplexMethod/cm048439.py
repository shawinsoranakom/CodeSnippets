def _compute_location_id(self):
        company_warehouses = self.env['stock.warehouse'].search([('company_id', 'in', self.company_id.ids)])
        if len(company_warehouses) == 0 and self.company_id:
            self.env['stock.warehouse']._warehouse_redirect_warning()
        groups = company_warehouses._read_group(
            [('company_id', 'in', self.company_id.ids)], ['company_id'], ['lot_stock_id:array_agg'])
        locations_per_company = {
            company.id: lot_stock_ids[0] if lot_stock_ids else False
            for company, lot_stock_ids in groups
        }
        for scrap in self:
            if scrap.picking_id:
                scrap.location_id = scrap.picking_id.location_dest_id if scrap.picking_id.state == 'done' else scrap.picking_id.location_id
            elif scrap.company_id:
                scrap.location_id = locations_per_company[scrap.company_id.id]