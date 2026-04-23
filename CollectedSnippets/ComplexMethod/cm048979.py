def write(self, vals):
        batches_to_rename = self.env['stock.picking.batch']
        if vals.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
            batches_to_rename = self.filtered(lambda b: b.picking_type_id != picking_type)
        res = super().write(vals)
        if not self.picking_ids:
            self.filtered(lambda b: b.state == 'in_progress').action_cancel()
        if vals.get('picking_type_id'):
            self._sanity_check()
            for batch in batches_to_rename:
                sequence_code = 'picking.wave' if batch.is_wave else 'picking.batch'
                batch.name = self._prepare_name(picking_type, sequence_code, batch.company_id)
        if vals.get('picking_ids'):
            batch_without_picking_type = self.filtered(lambda batch: not batch.picking_type_id)
            if batch_without_picking_type:
                picking = self.picking_ids and self.picking_ids[0]
                batch_without_picking_type.picking_type_id = picking.picking_type_id.id
        if 'user_id' in vals:
            self.picking_ids.assign_batch_user(vals['user_id'])
        return res