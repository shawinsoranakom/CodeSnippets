def _onchange_producing(self):
        production_move = self.move_finished_ids.filtered(
            lambda move: move.product_id == self.product_id
        )
        if not production_move:
            # Happens when opening the mo?
            return
        for line in production_move.move_line_ids:
            line.qty_done = 0
        qty_producing = self.qty_producing - self.qty_produced
        vals = production_move._set_quantity_done_prepare_vals(qty_producing)
        if vals['to_create']:
            for res in vals['to_create']:
                production_move.move_line_ids.new(res)
        if vals['to_write']:
            for move_line, res in vals['to_write']:
                move_line.update(res)

        for move in (self.move_raw_ids | self.move_finished_ids.filtered(lambda m: m.product_id != self.product_id)):
            new_qty = qty_producing * move.unit_factor
            for line in move.move_line_ids:
                line.qty_done = 0
            vals = move._set_quantity_done_prepare_vals(new_qty)
            if vals['to_create']:
                for res in vals['to_create']:
                    move.move_line_ids.new(res)
            if vals['to_write']:
                for move_line, res in vals['to_write']:
                    move_line.update(res)