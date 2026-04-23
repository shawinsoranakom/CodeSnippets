def get_move_line_quant_match(self, move_id, dirty_move_line_ids, dirty_quant_ids):
        # Since the quant_id field is neither stored nor computed, this method is used to compute the match if it exists
        move = self.env['stock.move'].browse(move_id)
        deleted_move_lines = move.move_line_ids - self
        dirty_move_lines = self.env['stock.move.line'].browse(dirty_move_line_ids)
        quants_data = []
        move_lines_data = []
        domain = Domain("id", "in", dirty_quant_ids) | Domain.OR(
            Domain([
                ("product_id", "=", move_line.product_id.id),
                ("lot_id", "=", move_line.lot_id.id),
                ("location_id", "=", move_line.location_id.id),
                ("package_id", "=", move_line.package_id.id),
                ("owner_id", "=", move_line.owner_id.id),
            ])
            for move_line in dirty_move_lines | deleted_move_lines
        )
        if not domain.is_false():
            quants = self.env['stock.quant'].search(domain)
            for quant in quants:
                dirty_lines = dirty_move_lines.filtered(lambda ml: ml.product_id == quant.product_id
                    and ml.lot_id == quant.lot_id
                    and ml.location_id == quant.location_id
                    and ml.package_id == quant.package_id
                    and ml.owner_id == quant.owner_id
                )
                deleted_lines = deleted_move_lines.filtered(lambda ml: ml.product_id == quant.product_id
                    and ml.lot_id == quant.lot_id
                    and ml.location_id == quant.location_id
                    and ml.package_id == quant.package_id
                    and ml.owner_id == quant.owner_id
                )
                quants_data.append((quant.id, {"available_quantity": quant.available_quantity + sum(ml.quantity_product_uom for ml in deleted_lines), "move_line_ids": dirty_lines.ids}))
                move_lines_data += [(ml.id, {"quantity": ml.quantity, "quant_id": quant.id}) for ml in dirty_lines]
        return [quants_data, move_lines_data]