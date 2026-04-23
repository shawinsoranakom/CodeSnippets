def _find_delivery_ids_by_lot(self, lot_path=None, delivery_by_lot=None):
        if lot_path is None:
            lot_path = set()
        domain = Domain([
            ('lot_id', 'in', self.ids),
            ('state', '=', 'done'),
        ]) & Domain(self._get_outgoing_domain())
        move_lines = self.env['stock.move.line'].search(domain)
        moves_by_lot = {
            lot_id: {'producing_lines': set(), 'barren_lines': set()}
            for lot_id in move_lines.lot_id.ids
        }
        for line in move_lines:
            if line.produce_line_ids:
                moves_by_lot[line.lot_id.id]['producing_lines'].add(line.id)
            else:
                moves_by_lot[line.lot_id.id]['barren_lines'].add(line.id)
        if delivery_by_lot is None:
            delivery_by_lot = dict()
        for lot in self:
            delivery_ids = set()

            if moves_by_lot.get(lot.id):
                producing_move_lines = self.env['stock.move.line'].browse(moves_by_lot[lot.id]['producing_lines'])
                barren_move_lines = self.env['stock.move.line'].browse(moves_by_lot[lot.id]['barren_lines'])

                if producing_move_lines:
                    lot_path.add(lot.id)
                    next_lots = producing_move_lines.produce_line_ids.lot_id.filtered(lambda l: l.id not in lot_path)
                    next_lots_ids = set(next_lots.ids)
                    # If some producing lots are in lot_path, it means that they have been previously processed.
                    # Their results are therefore already in delivery_by_lot and we add them to delivery_ids directly.
                    delivery_ids.update(*(delivery_by_lot.get(lot_id, []) for lot_id in (producing_move_lines.produce_line_ids.lot_id - next_lots).ids))

                    for lot_id, delivery_ids_set in next_lots._find_delivery_ids_by_lot(lot_path=lot_path, delivery_by_lot=delivery_by_lot).items():
                        if lot_id in next_lots_ids:
                            delivery_ids.update(delivery_ids_set)
                delivery_ids.update(barren_move_lines.picking_id.ids)

            delivery_by_lot[lot.id] = list(delivery_ids)
        return delivery_by_lot