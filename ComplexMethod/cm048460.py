def _compute_reference(self):
        for move in self:
            if move.scrap_id:
                move.reference = move.scrap_id.name
            elif move.is_inventory:
                if move.inventory_name:
                    move.reference = move.inventory_name
                else:
                    move.reference = _('Product Quantity Confirmed') if float_is_zero(move.quantity, precision_rounding=move.product_uom.rounding) else _('Product Quantity Updated')
                    if move.create_uid and move.create_uid.id != SUPERUSER_ID:
                        move.reference += f' ({move.create_uid.display_name})'
            else:
                move.reference = move.picking_id.name