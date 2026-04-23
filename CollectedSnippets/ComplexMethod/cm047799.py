def _get_moves_raw_values(self):
        moves = []
        for production in self:
            if not production.bom_id:
                continue
            factor = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id, round=False) / production.bom_id.product_qty
            _boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id, never_attribute_values=production.never_product_template_attribute_value_ids)
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or\
                        bom_line.product_id.type != 'consu':
                    continue
                operation = bom_line.operation_id.id or line_data['parent_line'] and line_data['parent_line'].operation_id.id
                moves.append(production._get_move_raw_values(
                    bom_line.product_id,
                    line_data['qty'],
                    bom_line.product_uom_id,
                    operation,
                    bom_line
                ))
        return moves