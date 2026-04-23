def _compute_locations(self):
        for production in self:
            if not production.picking_type_id.default_location_src_id or not production.picking_type_id.default_location_dest_id:
                company_id = production.company_id.id if (production.company_id and production.company_id in self.env.companies) else self.env.company.id
                fallback_loc = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1).lot_stock_id
            production.location_src_id = production.picking_type_id.default_location_src_id.id or fallback_loc.id
            production.location_dest_id = production.picking_type_id.default_location_dest_id.id or fallback_loc.id