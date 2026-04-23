def _compute_location_id(self):
        for line in self:
            if not line.location_id or line._origin.picking_id.location_id != line.picking_id.location_id:
                line.location_id = line.move_id.location_id or line.picking_id.location_id
            if not line.location_dest_id or line._origin.picking_id.location_dest_id != line.picking_id.location_dest_id:
                line.location_dest_id = line.move_id.location_dest_id or line.picking_id.location_dest_id