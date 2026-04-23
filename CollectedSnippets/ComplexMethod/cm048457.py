def _compute_location_id(self):
        for move in self:
            if move.picked:
                continue
            if not (location := move.location_id) or move.picking_id != move._origin.picking_id or move.picking_type_id != move._origin.picking_type_id:
                if move.picking_id:
                    location = move.picking_id.location_id
                elif move.picking_type_id:
                    location = move.picking_type_id.default_location_src_id
            move.location_id = location