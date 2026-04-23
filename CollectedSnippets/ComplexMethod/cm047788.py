def _compute_state(self):
        """ Compute the production state. This uses a similar process to stock
        picking, but has been adapted to support having no moves. This adaption
        includes some state changes outside of this compute.

        There exist 3 extra steps for production:
        - progress: At least one item is produced or consumed.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        for production in self:
            if not production.state or not production.product_uom_id or not (production.id or production._origin.id):
                production.state = 'draft'
            elif production.state == 'cancel' or (production.move_finished_ids and all(move.state == 'cancel' for move in production.move_finished_ids)):
                production.state = 'cancel'
            elif (
                production.state == 'done'
                or (production.move_raw_ids and all(move.state in ('cancel', 'done') for move in production.move_raw_ids))
                and all(move.state in ('cancel', 'done') for move in production.move_finished_ids)
            ):
                production.state = 'done'
            elif production.workorder_ids and all(wo_state in ('done', 'cancel') for wo_state in production.workorder_ids.mapped('state')):
                production.state = 'to_close'
            elif not production.workorder_ids and production.product_uom_id.compare(production.qty_producing, production.product_qty) >= 0:
                production.state = 'to_close'
            elif (
                any(wo_state in ('progress', 'done') for wo_state in production.workorder_ids.mapped('state'))
                or production.product_uom_id and not production.product_uom_id.is_zero(production.qty_producing)
                or any(production.move_raw_ids.mapped('picked'))
            ):
                production.state = 'progress'