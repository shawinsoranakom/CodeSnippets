def create(self, vals_list):
        for vals in vals_list:
            if (vals.get('quantity') or vals.get('move_line_ids')) and 'lot_ids' in vals:
                vals.pop('lot_ids')
            picking_id = self.env['stock.picking'].browse(vals.get('picking_id'))
            if picking_id.state == 'done' and vals.get('state') != 'done':
                vals['state'] = 'done'
            if vals.get('state') == 'done':
                vals['picked'] = True
        res = super().create(vals_list)
        res._update_orderpoints()
        res._set_references()
        return res