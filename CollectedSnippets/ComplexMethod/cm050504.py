def _link_owner_on_return_picking(self, lines):
        """This method tries to retrieve the owner of the returned product"""
        if lines and lines[0].order_id.refunded_order_id.picking_ids:
            returned_lines_picking = lines[0].order_id.refunded_order_id.picking_ids
            returnable_qty_by_product = {}
            for move_line in returned_lines_picking.move_line_ids:
                returnable_qty_by_product[(move_line.product_id.id, move_line.owner_id.id or 0)] = move_line.quantity
            for move in self.move_line_ids:
                for keys in returnable_qty_by_product:
                    if move.product_id.id == keys[0] and keys[1] and returnable_qty_by_product[keys] > 0:
                        move.write({'owner_id': keys[1]})
                        returnable_qty_by_product[keys] -= move.quantity