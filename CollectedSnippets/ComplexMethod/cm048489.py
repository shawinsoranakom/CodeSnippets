def _process_decrease(move, quantity):
            mls_to_unlink = set()
            # Since the move lines might have been created in a certain order to respect
            # a removal strategy, they need to be unreserved in the opposite order
            for ml in reversed(move.move_line_ids.sorted('id')):
                if self.env.context.get('unreserve_unpicked_only') and ml.picked:
                    continue
                if move.product_uom.is_zero(quantity):
                    break
                qty_ml_dec = min(ml.quantity, ml.product_uom_id._compute_quantity(quantity, ml.product_uom_id, round=False))
                if ml.product_uom_id.is_zero(qty_ml_dec):
                    continue
                if ml.product_uom_id.compare(ml.quantity, qty_ml_dec) == 0 and ml.state not in ['done', 'cancel']:
                    mls_to_unlink.add(ml.id)
                else:
                    ml.quantity -= qty_ml_dec
                quantity -= move.product_uom._compute_quantity(qty_ml_dec, move.product_uom, round=False)
            self.env['stock.move.line'].browse(mls_to_unlink).unlink()