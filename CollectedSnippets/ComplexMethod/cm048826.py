def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        """
        super()._cal_price(consumed_moves)

        work_center_cost = 0
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity > 0)
        if finished_move:
            if finished_move.product_id.cost_method not in ('fifo', 'average'):
                finished_move.price_unit = finished_move.product_id.standard_price
                return True
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                work_center_cost += work_order._cal_cost()
            quantity = finished_move.product_uom._compute_quantity(
                finished_move.quantity, finished_move.product_id.uom_id)
            extra_cost = self.extra_cost * quantity

            total_cost = sum(move.value for move in consumed_moves) + work_center_cost + extra_cost
            byproduct_moves = self.move_byproduct_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.quantity > 0)
            byproduct_cost_share = 0
            for byproduct in byproduct_moves:
                if byproduct.cost_share == 0:
                    continue
                byproduct_cost_share += byproduct.cost_share
                if byproduct.product_id.cost_method in ('fifo', 'average'):
                    byproduct.price_unit = total_cost * byproduct.cost_share / 100 / byproduct.product_uom._compute_quantity(byproduct.quantity, byproduct.product_id.uom_id)
            finished_move.price_unit = total_cost * float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001) / quantity
        return True