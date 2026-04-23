def _auto_wave_lines_into_existing_waves(self, nearest_parent_locations=False):
        """ Try to add move lines to existing waves if possible, return move lines of which no appropriate waves were found to link to
         :param nearest_parent_locations (defaultdict): the key is the move line and the value is the nearest parent location in the wave locations list"""
        remaining_lines = OrderedSet()
        batches_to_validate_ids = self.env.context.get('batches_to_validate', False)
        for (picking_type, lines) in self.grouped(lambda l: l.picking_type_id).items():
            if lines:
                domains = [
                    Domain('picking_type_id', '=', picking_type.id),
                    Domain('company_id', 'in', lines.mapped('company_id').ids),
                    Domain('is_wave', '=', True),
                ]
                if picking_type.batch_auto_confirm:
                    domains.append(Domain('state', 'not in', ['done', 'cancel']))
                else:
                    domains.append(Domain('state', '=', 'draft'))
                if picking_type.batch_group_by_partner:
                    domains.append(Domain('picking_ids.partner_id', 'in', lines.move_id.partner_id.ids))
                if picking_type.batch_group_by_destination:
                    domains.append(Domain('picking_ids.partner_id.country_id', 'in', lines.move_id.partner_id.country_id.ids))
                if picking_type.batch_group_by_src_loc:
                    domains.append(Domain('picking_ids.location_id', 'in', lines.location_id.ids))
                if picking_type.batch_group_by_dest_loc:
                    domains.append(Domain('picking_ids.location_dest_id', 'in', lines.location_dest_id.ids))
                if batches_to_validate_ids:
                    domains.append(Domain('id', 'not in', batches_to_validate_ids))
                domains = lines._get_potential_existing_waves_extra_domain(domains, picking_type)

                potential_waves = self.env['stock.picking.batch'].search(Domain.AND(domains))
                wave_to_new_lines = defaultdict(set)

                # These dictionaries are used to enforce batch max lines/transfers/weight limits
                # Each time a line is matched to a wave, we update the corresponding values
                wave_to_new_moves = defaultdict(set)
                waves_to_new_pickings = defaultdict(set)
                waves_new_extra_weight = defaultdict(float)

                waves_nearest_parent_locations = defaultdict(int)
                if picking_type.wave_group_by_location:
                    valid_wave_ids = set()
                    # We want to find the most descendant location in the wave locations list that is a parent of all the lines in each wave.
                    # We also want to exclude waves that have lines that are not in these locations.
                    for wave in potential_waves:
                        for wave_location in reversed(picking_type.wave_location_ids):
                            if all(loc._child_of(wave_location) for loc in wave.move_line_ids.location_id):
                                waves_nearest_parent_locations[wave] = wave_location.id
                                valid_wave_ids.add(wave.id)
                                break
                    potential_waves = self.env['stock.picking.batch'].browse(valid_wave_ids)

                for line in lines:
                    wave_found = False
                    for wave in potential_waves:
                        if line.company_id != wave.company_id \
                        or (picking_type.batch_group_by_partner and line.move_id.partner_id != wave.picking_ids.partner_id) \
                        or (picking_type.batch_group_by_destination and line.move_id.partner_id.country_id != wave.picking_ids.partner_id.country_id) \
                        or (picking_type.batch_group_by_src_loc and line.location_id != wave.picking_ids.location_id) \
                        or (picking_type.batch_group_by_dest_loc and line.location_dest_id != wave.picking_ids.location_dest_id) \
                        or (picking_type.wave_group_by_product and line.product_id != wave.move_line_ids.product_id) \
                        or (picking_type.wave_group_by_category and line.product_id.categ_id != wave.move_line_ids.product_id.categ_id) \
                        or (picking_type.wave_group_by_location and waves_nearest_parent_locations[wave] != nearest_parent_locations[line].id) \
                        or not line._is_potential_existing_wave_extra(wave):
                            continue

                        wave_new_move_ids = wave_to_new_moves[wave]
                        wave_new_picking_ids = waves_to_new_pickings[wave]
                        wave_move_ids = set(wave.move_line_ids.mapped('move_id.id'))
                        wave_picking_ids = set(wave.move_line_ids.mapped('picking_id.id'))
                        # `is_line_auto_mergeable` is a method that checks if the line can be added to the wave without exceeding the limits
                        # It takes as arguments the number of new moves that will be added to the wave, the number of new pickings that will be added to the wave
                        # and the extra weight that will be added to the wave. So we need to check that the move/picking of the line is not already in the wave
                        # so that we don't count them as new moves/pickings.
                        if not wave._is_line_auto_mergeable(
                            line.move_id.id not in wave_move_ids and line.move_id.id not in wave_new_move_ids and len(wave_new_move_ids) + 1,
                            line.picking_id.id not in wave_picking_ids and line.picking_id.id not in wave_new_picking_ids and len(wave_new_picking_ids) + 1,
                            waves_new_extra_weight[wave] + line.product_id.weight * line.quantity_product_uom
                        ):
                            continue

                        if line.move_id.id not in wave_move_ids:
                            wave_to_new_moves[wave].add(line.move_id.id)
                        if line.picking_id.id not in wave_picking_ids:
                            waves_to_new_pickings[wave].add(line.picking_id.id)
                        waves_new_extra_weight[wave] += line.product_id.weight * line.quantity_product_uom
                        wave_to_new_lines[wave].add(line.id)
                        wave_found = True
                        break
                    if not wave_found:
                        remaining_lines.add(line.id)
                for wave, line_ids in wave_to_new_lines.items():
                    lines = self.env['stock.move.line'].browse(line_ids)
                    lines._add_to_wave(wave)
        return list(remaining_lines)