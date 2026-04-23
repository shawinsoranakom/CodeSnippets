def write(self, vals):
        if vals.get('picking_type_id') and any(picking.state in ('done', 'cancel') for picking in self):
            raise UserError(_("Changing the operation type of this record is forbidden at this point."))
        if vals.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
            for picking in self:
                if picking.picking_type_id != picking_type:
                    picking.name = picking_type.sequence_id.next_by_id()
                    vals['location_id'] = picking_type.default_location_src_id.id
                    vals['location_dest_id'] = picking_type.default_location_dest_id.id
        res = super().write(vals)
        if vals.get('date_done'):
            self.filtered(lambda p: p.state == 'done').move_ids.date = vals['date_done']
        if vals.get('signature'):
            for picking in self:
                picking._attach_sign()
        # Change locations of moves if those of the picking change
        after_vals = {}
        if vals.get('location_id'):
            after_vals['location_id'] = vals['location_id']
        if vals.get('location_dest_id'):
            after_vals['location_dest_id'] = vals['location_dest_id']
        if 'partner_id' in vals:
            after_vals['partner_id'] = vals['partner_id']
        if after_vals:
            self.move_ids.filtered(lambda move: move.location_dest_usage != 'inventory').write(after_vals)
        if vals.get('move_ids'):
            self._autoconfirm_picking()

        return res