def _add_to_wave(self, wave=False, description=False):
        """ Detach lines (and corresponding stock move from a picking to another). If wave is
        passed, attach new picking into it. If not attach line to their original picking.

        :param int wave: id of the wave picking on which to put the move lines. """

        if not wave:
            wave = self.env['stock.picking.batch'].create({
                'is_wave': True,
                'picking_type_id': self.picking_type_id and self.picking_type_id[0].id,
                'user_id': self.env.context.get('active_owner_id'),
                'description': description,
            })
            notification_title = _('The following wave transfer has been created')
        else:
            notification_title = _('The following wave transfer has been updated')
        line_by_picking = defaultdict(lambda: self.env['stock.move.line'])
        for line in self:
            line_by_picking[line.picking_id] |= line
        picking_to_wave_vals_list = []
        split_pickings_ids = set()
        for picking, lines in line_by_picking.items():
            # Move the entire picking if all the line are taken
            line_by_move = defaultdict(lambda: self.env['stock.move.line'])
            qty_by_move = defaultdict(float)
            for line in lines:
                move = line.move_id
                line_by_move[move] |= line
                qty = line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id, rounding_method='HALF-UP')
                qty_by_move[line.move_id] += qty

            # If all moves are to be transferred to the wave, link the picking to the wave
            if lines == picking.move_line_ids and lines.move_id == picking.move_ids:
                add_all_moves = True
                for move, qty in qty_by_move.items():
                    if move.product_uom.is_zero(qty):
                        add_all_moves = False
                        break
                if add_all_moves:
                    wave.picking_ids = [Command.link(picking.id)]
                    continue

            # Split the picking in two part to extract only line that are taken on the wave
            picking_to_wave_vals = picking.copy_data({
                'move_ids': [],
                'move_line_ids': [],
                'batch_id': wave.id,
                'scheduled_date': picking.scheduled_date,
            })[0]
            split_pickings_ids.add(picking.id)
            for move, move_lines in line_by_move.items():
                picking_to_wave_vals['move_line_ids'] += [Command.link(line.id) for line in lines]
                # if all the line of a stock move are taken we change the picking on the stock move
                if move_lines == move.move_line_ids:
                    picking_to_wave_vals['move_ids'] += [Command.link(move.id)]
                    continue
                # Split the move
                qty = qty_by_move[move]
                new_move = move._split(qty)
                new_move[0]['move_line_ids'] = [Command.set(move_lines.ids)]
                picking_to_wave_vals['move_ids'] += [Command.create(new_move[0])]

            picking_to_wave_vals_list.append(picking_to_wave_vals)

        if picking_to_wave_vals_list:
            split_pickings = self.env['stock.picking'].browse(split_pickings_ids) | self.env['stock.picking'].create(picking_to_wave_vals_list)
            split_pickings._add_to_wave_post_picking_split_hook()
        if wave.picking_type_id.batch_auto_confirm:
            wave.action_confirm()
        if not self.env.context.get('from_wave_form'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': notification_title,
                    'message': '%s',
                    'links': [{
                        'label': wave.name,
                        'url': f'/odoo/action-stock_picking_batch.action_picking_tree_wave/{wave.id}',
                    }],
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'soft_reload',
            }