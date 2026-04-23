def _compute_picking_type_id(self):
        domain = [
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', 'in', self.company_id.ids),
        ]
        picking_types = self.env['stock.picking.type'].search_read(domain, ['company_id'], load=False, limit=1)
        picking_type_by_company = {pt['company_id']: pt['id'] for pt in picking_types}
        default_picking_type_id = self.env.context.get('default_picking_type_id')
        default_picking_type = default_picking_type_id and self.env['stock.picking.type'].browse(default_picking_type_id)
        if not default_picking_type:
            default_warehouse_id = self.env.context.get('force_warehouse_id')
            default_picking_type = default_warehouse_id and self.env['stock.warehouse'].browse(default_warehouse_id).manu_type_id
        for mo in self:
            if default_picking_type and default_picking_type.company_id == mo.company_id:
                mo.picking_type_id = default_picking_type
                continue
            if mo.bom_id and mo.bom_id.picking_type_id:
                mo.picking_type_id = mo.bom_id.picking_type_id
                continue
            if mo.picking_type_id and mo.picking_type_id.company_id == mo.company_id:
                continue
            mo.picking_type_id = picking_type_by_company.get(mo.company_id.id, False)
            company_warehouse = self.env['stock.warehouse'].search([('company_id', '=', mo.company_id.id)], limit=1)
            if not company_warehouse:
                self.env['stock.warehouse']._warehouse_redirect_warning()