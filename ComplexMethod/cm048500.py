def action_unassign(self, move_id, qty, in_ids):
        """ Unassign moves [i.e. unlink] from a move (i.e. make non-MTO)
        :param move_id id: the id of the move to make non-MTO
        :param qty float: the total quantity that is being unassigned from move_id
        :param in_ids ids: the ids of the moves that are to be unassigned from move_id
        """
        out = self.env['stock.move'].browse(move_id)
        ins = self.env['stock.move'].browse(in_ids)

        amount_unassigned = 0
        for in_move in ins:
            if out.id not in in_move.move_dest_ids.ids:
                continue
            move_quantity = in_move.product_qty or in_move.product_uom._compute_quantity(in_move.quantity, in_move.product_id.uom_id, rounding_method='HALF-UP')
            in_move.move_dest_ids -= out
            self._action_unassign(in_move, out)
            amount_unassigned += min(qty, move_quantity)
            if out.product_id.uom_id.compare(qty, amount_unassigned) <= 0:
                break
        if out.move_orig_ids and out.state != 'done':
            # annoying use cases where we need to split the out move:
            # 1. batch reserved + individual picking unreserved
            # 2. moves linked from backorder generation
            total_still_linked = sum(out.move_orig_ids.mapped('product_qty'))
            new_move_vals = out._split(total_still_linked)
            if new_move_vals:
                new_move_vals[0]['procure_method'] = 'make_to_order'
                new_move_vals[0]['reservation_date'] = out.reservation_date
                new_out = self.env['stock.move'].create(new_move_vals)
                # don't do action confirm to avoid creating additional unintentional reservations
                new_out.write({'state': 'confirmed'})
                out.move_line_ids.move_id = new_out
                (out | new_out)._compute_quantity()
                if new_out.quantity > new_out.product_qty:
                    # extra reserved amount goes to no longer linked out
                    reserved_amount_to_remain = new_out.quantity - new_out.product_qty
                    for move_line_id in new_out.move_line_ids:
                        if reserved_amount_to_remain <= 0:
                            break
                        if move_line_id.quantity_product_uom > reserved_amount_to_remain:
                            new_move_line = move_line_id.copy({'quantity': 0})
                            new_move_line.quantity = out.product_id.uom_id._compute_quantity(move_line_id.quantity_product_uom - reserved_amount_to_remain, move_line_id.product_uom_id, rounding_method='HALF-UP')
                            move_line_id.quantity -= new_move_line.quantity
                            move_line_id.move_id = out
                            break
                        else:
                            move_line_id.move_id = out
                            reserved_amount_to_remain -= move_line_id.quantity_product_uom
                    (out | new_out)._compute_quantity()
                out.move_orig_ids = False
                new_out._recompute_state()
        out.procure_method = 'make_to_stock'
        out._do_unreserve()
        return True