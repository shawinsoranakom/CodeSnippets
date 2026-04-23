def _compute_reference(self):
        moves_with_reference = self.env['stock.move']
        for move in self:
            if move.raw_material_production_id and move.raw_material_production_id.name:
                move.reference = move.raw_material_production_id.name
                moves_with_reference |= move
            if move.production_id and move.production_id.name:
                move.reference = move.production_id.name
                moves_with_reference |= move
            if move.unbuild_id and move.unbuild_id.name:
                move.reference = move.unbuild_id.name
                moves_with_reference |= move
        super(StockMove, self - moves_with_reference)._compute_reference()