def _assign_picking_values(self, picking):
        vals = {}
        if any(picking.partner_id != m.partner_id for m in self):
            vals['partner_id'] = False
        if any(picking.origin != m.origin for m in self):
            current_origins = picking.origin.split(',') if picking.origin else []
            new_moves_origins = [move.origin for move in self if move.origin]
            new_origin = ','.join(OrderedSet(current_origins + new_moves_origins))
            if picking.origin != new_origin:
                vals['origin'] = new_origin
        return vals