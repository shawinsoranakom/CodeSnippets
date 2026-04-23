def write(self, vals):
        res = super().write(vals)
        repair_moves = self.env['stock.move']
        moves_to_create_so_line = self.env['stock.move']
        for move in self:
            if not move.repair_id:
                continue
            # checks vals update
            if not move.sale_line_id and 'sale_line_id' not in vals and move.repair_line_type == 'add':
                moves_to_create_so_line |= move
            if move.sale_line_id and ('repair_line_type' in vals or 'product_uom_qty' in vals):
                repair_moves |= move

        repair_moves._update_repair_sale_order_line()
        moves_to_create_so_line._create_repair_sale_order_line()
        return res