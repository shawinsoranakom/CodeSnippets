def _compute_description_picking(self):
        super()._compute_description_picking()
        bom_line_description = {}
        for bom in self.bom_line_id.bom_id:
            if bom.type != 'phantom':
                continue
            # mapped('id') to keep NewId
            line_ids = self.bom_line_id.filtered(lambda line: line.bom_id == bom).mapped('id')
            total = len(line_ids)
            for i, line_id in enumerate(line_ids):
                bom_line_description[line_id] = '%s - %d/%d' % (bom.display_name, i + 1, total)

        for move in self:
            if not move.description_picking_manual and move.bom_line_id.id in bom_line_description:
                if move.description_picking == move.product_id.display_name:
                    move.description_picking = ''
                move.description_picking += ('\n' if move.description_picking else '') + bom_line_description.get(move.bom_line_id.id)