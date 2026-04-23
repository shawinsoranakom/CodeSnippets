def _auto_wave_lines_into_new_waves(self, nearest_parent_locations=False):
        """ Create new waves for the move lines that could not be added to existing waves. """
        picking_types = self.picking_type_id
        for picking_type in picking_types:
            lines = self.filtered(lambda l: l.picking_type_id == picking_type)
            domains = [Domain([
                ('id', 'in', lines.ids),
                ('company_id', 'in', self.company_id.ids),
                ('picking_id.state', '=', 'assigned'),
                ('picking_type_id', '=', picking_type.id),
                '|',
                ('batch_id', '=', False),
                ('batch_id.is_wave', '=', False),
            ])]
            if picking_type.batch_group_by_partner:
                domains.append(Domain('move_id.partner_id', 'in', lines.move_id.partner_id.ids))
            if picking_type.batch_group_by_destination:
                domains.append(Domain('move_id.partner_id.country_id', 'in', lines.move_id.partner_id.country_id.ids))
            if picking_type.batch_group_by_src_loc:
                domains.append(Domain('location_id', 'in', lines.location_id.ids))
            if picking_type.batch_group_by_dest_loc:
                domains.append(Domain('location_dest_id', 'in', lines.location_dest_id.ids))
            if picking_type.wave_group_by_product:
                domains.append(Domain('product_id', 'in', lines.product_id.ids))
            if picking_type.wave_group_by_category:
                domains.append(Domain('product_id.categ_id', 'in', lines.product_id.categ_id.ids))
            if picking_type.wave_group_by_location:
                domains.append(Domain('location_id', 'child_of', picking_type.wave_location_ids.ids))
            domains = lines._get_potential_new_waves_extra_domain(domains, picking_type)

            potential_lines = self.env['stock.move.line'].search(Domain.AND(domains))
            lines_nearest_parent_locations = defaultdict(int)
            if picking_type.wave_group_by_location:
                for line in potential_lines:
                    for location in reversed(picking_type.wave_location_ids):
                        if line.location_id._child_of(location):
                            lines_nearest_parent_locations[line] = location.id
                            break

            line_to_lines = defaultdict(set)
            matched_lines = set()
            remaining_line_ids = OrderedSet()
            for line in lines:
                lines_found = False
                if line.id in matched_lines:
                    continue
                for potential_line in potential_lines:
                    if line.id == potential_line.id \
                    or line.company_id != potential_line.company_id \
                    or (picking_type.batch_group_by_partner and line.move_id.partner_id != potential_line.move_id.partner_id) \
                    or (picking_type.batch_group_by_destination and line.move_id.partner_id.country_id != potential_line.move_id.partner_id.country_id) \
                    or (picking_type.batch_group_by_src_loc and line.location_id != potential_line.location_id) \
                    or (picking_type.batch_group_by_dest_loc and line.location_dest_id != potential_line.location_dest_id) \
                    or (picking_type.wave_group_by_product and line.product_id != potential_line.product_id) \
                    or (picking_type.wave_group_by_category and line.product_id.categ_id != potential_line.product_id.categ_id) \
                    or (picking_type.wave_group_by_location and lines_nearest_parent_locations[potential_line] != nearest_parent_locations[line].id)  \
                    or not line._is_new_potential_line_extra(potential_line):
                        continue

                    line_to_lines[line].add(potential_line.id)
                    matched_lines.add(potential_line.id)
                    lines_found = True
                if not lines_found:
                    remaining_line_ids.add(line.id)

            for line, potential_line_ids in line_to_lines.items():
                if line.batch_id.is_wave:
                    continue

                potential_lines = self.env['stock.move.line'].browse(potential_line_ids | {line.id})

                # We want to make sure that batch/wave limits specified in the picking type are respected.
                # We want also to reduce picking splits as much as possible. So we try to group as much as possible by sorting the lines by picking and move.
                potential_lines = potential_lines.sorted(key=lambda l: (l.picking_id.id, l.move_id.id))

                while potential_lines:
                    new_wave = self.env['stock.picking.batch'].create({
                        'is_wave': True,
                        'picking_type_id': picking_type.id,
                        'description': line._get_auto_wave_description(nearest_parent_locations[line]),
                    })
                    wave_move_ids = set()
                    wave_picking_ids = set()
                    wave_weight = 0

                    wave_line_ids = set()

                    for potential_line in potential_lines:
                        if potential_line.batch_id.is_wave:
                            continue
                        wave_move_ids.add(potential_line.move_id.id)
                        wave_picking_ids.add(potential_line.picking_id.id)
                        wave_weight += potential_line.product_id.weight * potential_line.quantity_product_uom
                        if new_wave._is_line_auto_mergeable(
                            len(wave_move_ids),
                            len(wave_picking_ids),
                            wave_weight
                        ):
                            wave_line_ids.add(potential_line.id)
                        else:
                            break
                    wave_lines = self.env['stock.move.line'].browse(wave_line_ids)
                    wave_lines._add_to_wave(new_wave)
                    potential_lines -= wave_lines

            remaining_lines = self.env['stock.move.line'].browse(remaining_line_ids)
            remaining_waves = self.env['stock.picking.batch'].create([{
                'is_wave': True,
                'picking_type_id': picking_type.id,
                'description': remaining_line._get_auto_wave_description(nearest_parent_locations[remaining_line]),
            } for remaining_line in remaining_lines])
            for (line, wave) in zip(remaining_lines, remaining_waves):
                line._add_to_wave(wave)