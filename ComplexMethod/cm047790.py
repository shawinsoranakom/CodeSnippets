def _compute_reservation_state(self):
        for production in self:
            if production.state in ('draft', 'done', 'cancel'):
                production.reservation_state = False
                continue
            relevant_move_state = production.move_raw_ids.filtered(
                lambda m: (
                    m.product_id
                    and not (
                        m.picked
                        or m.product_uom.is_zero(
                            m.product_uom_qty,
                        )
                    )
                )
            )._get_relevant_state_among_moves()
            # Compute reservation state according to its component's moves.
            if relevant_move_state == 'partially_available':
                if production.workorder_ids.operation_id and production.bom_id.ready_to_produce == 'asap':
                    production.reservation_state = production._get_ready_to_produce_state()
                else:
                    production.reservation_state = 'confirmed'
            elif relevant_move_state != 'draft':
                production.reservation_state = relevant_move_state
            else:
                production.reservation_state = False