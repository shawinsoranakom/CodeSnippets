def _auto_wave(self):
        """ Try to find compatible waves to attach the move lines to, otherwise create new waves when possible/appropriate. """
        wave_locs_by_picking_type = {}
        for picking_type in self.picking_type_id:
            if not picking_type.wave_group_by_location:
                continue
            if picking_type in wave_locs_by_picking_type:
                continue
            wave_locs_by_picking_type[picking_type] = set(picking_type.wave_location_ids.ids)
        lines_nearest_parent_locations = defaultdict(lambda: self.env['stock.location'])
        batchable_line_ids = OrderedSet()
        for line in self:
            if not line._is_auto_waveable():
                continue
            if not line.picking_type_id.wave_group_by_location:
                batchable_line_ids.add(line.id)
                continue
            # We want to find the most descendant location in the wave locations list that is a parent of the line location.
            # Since the wave locations are ordered by complete_name (from the most descendant to the most ancestor), we can iterate in reverse order.
            wave_locs_set = wave_locs_by_picking_type[line.picking_type_id]
            loc = line.location_id
            while (loc):
                if loc.id in wave_locs_set:
                    lines_nearest_parent_locations[line] = loc
                    batchable_line_ids.add(line.id)
                    break
                loc = loc.location_id
        batchable_lines = self.env['stock.move.line'].browse(batchable_line_ids)

        remaining_line_ids = batchable_lines._auto_wave_lines_into_existing_waves(nearest_parent_locations=lines_nearest_parent_locations)
        remaining_lines = self.env['stock.move.line'].browse(remaining_line_ids)
        if remaining_lines:
            remaining_lines._auto_wave_lines_into_new_waves(nearest_parent_locations=lines_nearest_parent_locations)