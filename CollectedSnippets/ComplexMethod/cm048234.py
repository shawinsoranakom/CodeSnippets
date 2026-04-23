def _update_repair_sale_order_line(self):
        if not self:
            return
        moves_to_clean = self.env['stock.move']
        moves_to_update = self.env['stock.move']
        for move in self:
            if not move.repair_id:
                continue
            if move.sale_line_id and move.repair_line_type != 'add':
                moves_to_clean |= move
            if move.sale_line_id and move.repair_line_type == 'add':
                moves_to_update |= move
        moves_to_clean._clean_repair_sale_order_line()
        for sale_line, _ in groupby(moves_to_update, lambda m: m.sale_line_id):
            sale_line.product_uom_qty = sum(sale_line.move_ids.mapped('product_uom_qty'))