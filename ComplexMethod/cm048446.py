def _compute_location_id(self):
        for picking in self:
            if picking.state in ('cancel', 'done') or picking.return_id:
                continue
            picking = picking.with_company(picking.company_id)
            if picking.picking_type_id:
                location_src = picking.picking_type_id.default_location_src_id
                if location_src.usage == 'supplier' and picking.partner_id:
                    location_src = picking.partner_id.property_stock_supplier
                location_dest = picking.picking_type_id.default_location_dest_id
                if location_dest.usage == 'customer' and picking.partner_id:
                    location_dest = picking.partner_id.property_stock_customer
                picking.location_id = location_src.id
                picking.location_dest_id = location_dest.id