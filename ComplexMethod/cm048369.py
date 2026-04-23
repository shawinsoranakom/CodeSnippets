def _find_delivery_ids_by_lot_iterative(self):
        """ Retrieve all delivery IDs (outgoing picking) linked to the lots
            in self and all the lots found when parcouring the produce lines.
            :return: A dictionary where keys are the IDs of the original 'stock.lot'
                      records (self) and values are lists of associated 'stock.picking' IDs.
            :rtype: dict
        """

        all_lot_ids = set(self.ids)
        barren_lines = defaultdict(set)
        parent_map = defaultdict(set)

        # Prefetch the lines linked to lots and split them between producing lines
        # and barren lines (lines that have `produce_line_ids` and lines that don't
        # have them respectively) and build the map of the parents of each lot (so we
        # can browse the tree from the leaves to the root and propagate the pickings)
        queue = list(self.ids)
        while queue:
            domain = Domain([
                ('lot_id', 'in', queue),
                ('state', '=', 'done'),
            ]) & Domain(self._get_outgoing_domain())

            queue = []
            move_lines = self.env['stock.move.line'].search(domain)
            for line in move_lines:
                lot_id = line.lot_id.id

                produce_line_lot_ids = line.produce_line_ids.lot_id.ids
                if produce_line_lot_ids:
                    for child_lot_id in produce_line_lot_ids:
                        parent_map[child_lot_id].add(lot_id)
                else:
                    barren_lines[lot_id].add(line.id)

                next_lots = set(produce_line_lot_ids) - all_lot_ids
                all_lot_ids.update(next_lots)
                queue.extend(next_lots)

        # Initialize delivery_by_lot with barren lines (i.e. the leaves of the lot tree)
        lots_to_propagate = set()
        delivery_by_lot = {lot_id: set() for lot_id in all_lot_ids}
        for lot_id in barren_lines:
            barren_line_ids = barren_lines[lot_id]
            if barren_line_ids:
                barren_move_lines = self.env['stock.move.line'].browse(barren_line_ids)
                delivery_by_lot[lot_id].update(barren_move_lines.picking_id.ids)
                lots_to_propagate.add(lot_id)

        # Propagate the deliveries from the children to their parent lots.
        # This loop processes lots whose delivery sets have just been updated,
        # ensuring the new results are merged upward through the parent graph until
        # all deliveries are propagated
        while lots_to_propagate:
            lot_id = lots_to_propagate.pop()

            for parent_id in parent_map.get(lot_id, []):
                new_deliveries = delivery_by_lot[lot_id] - delivery_by_lot[parent_id]
                if new_deliveries:
                    delivery_by_lot[parent_id].update(new_deliveries)
                    lots_to_propagate.add(parent_id)

        return {lot_id: list(delivery_by_lot[lot_id]) for lot_id in delivery_by_lot}