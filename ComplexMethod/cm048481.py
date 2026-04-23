def _action_cancel(self):
        if any(move.state == 'done' and move.location_dest_usage != 'inventory' for move in self):
            raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'. Create a return in order to reverse the moves which took place.'))
        moves_to_cancel = self.filtered(lambda m: m.state != 'cancel' and not (m.state == 'done' and m.location_dest_usage == 'inventory'))
        moves_to_cancel.picked = False
        # self cannot contain moves that are either cancelled or done, therefore we can safely
        # unlink all associated move_line_ids
        moves_to_cancel._do_unreserve()
        cancel_moves_origin = self.env['ir.config_parameter'].sudo().get_param('stock.cancel_moves_origin')

        moves_to_cancel.state = 'cancel'

        for move in moves_to_cancel:
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            if move.propagate_cancel:
                # only cancel the next move if all my siblings are also cancelled
                if all(state == 'cancel' for state in siblings_states):
                    move_dest_to_cancel = move.move_dest_ids.filtered(lambda m: m.state != 'done' and move.location_dest_id == m.location_id)
                    move_dest_to_cancel._action_cancel()
                    # Unlink from dest if dest is not in the chain
                    (move.move_dest_ids - move_dest_to_cancel).write({
                        'procure_method': 'make_to_stock',
                        'move_orig_ids': [Command.unlink(move.id)]
                    })
                    if cancel_moves_origin:
                        move.move_orig_ids.sudo().filtered(lambda m: m.state != 'done')._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move_dest_ids = move.move_dest_ids
                    move_dest_ids.write({
                        'procure_method': 'make_to_stock',
                        'move_orig_ids': [Command.unlink(move.id)]
                    })
        if not self.env.context.get('skip_cancel_activity'):
            # log an activity on the non-cancelled origin to warn the user that some actions might be required
            moves_to_cancel._log_cancel_activity()
        moves_to_cancel.write({
            'move_orig_ids': [(5, 0, 0)],
            'procure_method': 'make_to_stock',
        })
        return True