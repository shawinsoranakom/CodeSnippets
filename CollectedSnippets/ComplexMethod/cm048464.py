def _compute_show_info(self):
        for move in self:
            move.show_quant = move.picking_code != 'incoming'\
                           and move.product_id.is_storable
            move.show_lots_text = move.has_tracking != 'none'\
                and move.picking_type_id.use_create_lots\
                and not move.picking_type_id.use_existing_lots\
                and move.state != 'done' \
                and not move.origin_returned_move_id.id
            move.show_lots_m2o = not move.show_quant\
                and not move.show_lots_text\
                and move.has_tracking != 'none'\
                and (move.picking_type_id.use_existing_lots or move.state == 'done' or move.origin_returned_move_id.id)