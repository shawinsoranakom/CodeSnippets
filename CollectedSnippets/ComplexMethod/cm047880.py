def _add_origins_to_forecast(self, forecast_lines):
        # Keeps the link to its origin even when the product is now in stock.
        new_lines = []
        for line in filter(lambda line: not line.get('document_in', False) and line.get('move_out', False) and line.get('replenishment_filled', False), forecast_lines):
            move_out_qty = line['move_out'].product_uom._compute_quantity(line['move_out'].product_uom_qty, line['uom_id'])
            for move_origin in self.env['stock.move'].browse(line['move_out']._rollup_move_origs()):
                doc_origin = self._get_origin(move_origin)
                if doc_origin:
                    # Remove 'in_transit' for MTO replenishments
                    line['in_transit'] = False
                    move_origin_qty = move_origin.product_uom._compute_quantity(move_origin.product_uom_qty, line['uom_id'])
                    # Move quantity matches forecast, can add origin to the line
                    if float_compare(line['quantity'], move_origin_qty, precision_rounding=line['uom_id'].rounding) == 0:
                        line['document_in'] = {'_name': doc_origin._name, 'id': doc_origin.id}
                        line['move_in'] = move_origin
                        break

                    # Quantity doesn't match, either multiple origins for a single line or multiple lines for a single origin
                    used_quantity = min(move_out_qty, move_origin_qty)
                    new_line = copy.copy(line)
                    new_line['quantity'] = used_quantity
                    new_line['document_in'] = {'_name': doc_origin._name, 'id': doc_origin.id}
                    new_line['move_in'] = move_origin
                    new_lines.append(new_line)
                    # Remove used quantity from original forecast line
                    line['quantity'] -= used_quantity

                    move_out_qty -= used_quantity
                    if line['move_out'].product_uom.compare(move_out_qty, 0) <= 0:
                        break
        return new_lines + forecast_lines