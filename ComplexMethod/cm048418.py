def _run_push(self, move):
        """ Apply a push rule on a move.
        If the rule is 'no step added' it will modify the destination location
        on the move.
        If the rule is 'manual operation' it will generate a new move in order
        to complete the section define by the rule.
        Care this function is not call by method run. It is called explicitely
        in stock_move.py inside the method _push_apply
        """
        self.ensure_one()
        new_date = self._get_push_new_date(move)
        if self.auto == 'transparent':
            old_dest_location = move.location_dest_id
            move.write({'date': new_date, 'location_dest_id': self.location_dest_id.id})
            # make sure the location_dest_id is consistent with the move line location dest
            if move.move_line_ids:
                move.move_line_ids.location_dest_id = move.location_dest_id._get_putaway_strategy(move.product_id) or move.location_dest_id

            # avoid looping if a push rule is not well configured; otherwise call again push_apply to see if a next step is defined
            if self.location_dest_id != old_dest_location:
                # TDE FIXME: should probably be done in the move model IMO
                return move._push_apply()[:1]
        else:
            new_move_vals = self._push_prepare_move_copy_values(move, new_date)
            new_move = move.sudo().copy(new_move_vals)
            # when no more push we should reach final destination
            if new_move._skip_push():
                new_move.write({'location_dest_id': new_move.location_final_id.id})
            if new_move._should_bypass_reservation():
                new_move.write({'procure_method': 'make_to_stock'})
            if not new_move.location_id.should_bypass_reservation():
                move.sudo().write({'move_dest_ids': [(4, new_move.id)]})
            return new_move