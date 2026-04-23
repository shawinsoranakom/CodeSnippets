def _compute_show_allocation(self):
        self.show_allocation = False
        if not self.env.user.has_group('mrp.group_mrp_reception_report'):
            return
        for mo in self:
            if not mo.picking_type_id:
                return
            lines = mo.move_finished_ids.filtered(lambda m: m.product_id.is_storable and m.state != 'cancel')
            if lines:
                allowed_states = ['confirmed', 'partially_available', 'waiting']
                if mo.state == 'done':
                    allowed_states += ['assigned']
                wh_location_ids = self.env['stock.location']._search([('id', 'child_of', mo.picking_type_id.warehouse_id.view_location_id.id), ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search_count([
                    ('state', 'in', allowed_states),
                    ('product_qty', '>', 0),
                    ('location_id', 'in', wh_location_ids),
                    ('raw_material_production_id', 'not in', mo.ids),
                    ('product_id', 'in', lines.product_id.ids),
                    '|', ('move_orig_ids', '=', False),
                        ('move_orig_ids', 'in', lines.ids)], limit=1):
                    mo.show_allocation = True