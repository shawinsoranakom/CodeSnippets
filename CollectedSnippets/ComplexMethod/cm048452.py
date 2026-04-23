def _pre_action_done_hook(self):
        for picking in self:
            has_quantity = False
            has_pick = False
            for move in picking.move_ids:
                if move.quantity:
                    has_quantity = True
                if move.location_dest_usage == 'inventory':
                    continue
                if move.picked:
                    has_pick = True
                if has_quantity and has_pick:
                    break
            if has_quantity and not has_pick:
                picking.move_ids.picked = True
        if not self.env.context.get('skip_backorder'):
            pickings_to_backorder = self._check_backorder()
            if pickings_to_backorder:
                return pickings_to_backorder._action_generate_backorder_wizard(show_transfers=self._should_show_transfers())
        return True