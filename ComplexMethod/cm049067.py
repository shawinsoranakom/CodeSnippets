def create(self, vals_list):
        lot_ids = set()
        product_ids = set()
        move_ids = set()

        for vals in vals_list:
            if vals.get('move_id'):
                move_ids.add(vals['move_id'])
            elif vals.get('lot_id'):
                lot_ids.add(vals['lot_id'])
            else:
                product_ids.add(vals['product_id'])
        if lot_ids:
            move_ids.update(self.env['stock.move.line'].search([('lot_id', 'in', lot_ids)]).move_id.ids)
        products = self.env['product.product'].browse(product_ids)
        if products:
            moves_by_product = products._get_remaining_moves()
            for qty_by_move in moves_by_product.values():
                move_ids.update(self.env['stock.move'].concat(*qty_by_move.keys()).ids)

        res = super().create(vals_list)
        if move_ids:
            self.env['stock.move'].browse(move_ids)._set_value()
        return res