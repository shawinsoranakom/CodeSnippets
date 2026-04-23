def _free_reservation(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, ml_ids_to_ignore=None):
        """ When editing a done move line or validating one with some forced quantities, it is
        possible to impact quants that were not reserved. It is therefore necessary to edit or
        unlink the move lines that reserved a quantity now unavailable.

        :param ml_ids_to_ignore: OrderedSet of `stock.move.line` ids that should NOT be unreserved
        """
        self.ensure_one()
        if ml_ids_to_ignore is None:
            ml_ids_to_ignore = OrderedSet()
        ml_ids_to_ignore |= self.ids

        if self.move_id._should_bypass_reservation(location_id):
            return

        # We now have to find the move lines that reserved our now unavailable quantity. We
        # take care to exclude ourselves and the move lines were work had already been done.
        outdated_move_lines_domain = [
            ('state', 'not in', ['done', 'cancel']),
            ('product_id', '=', product_id.id),
            ('lot_id', '=', lot_id.id if lot_id else False),
            ('location_id', '=', location_id.id),
            ('owner_id', '=', owner_id.id if owner_id else False),
            ('package_id', '=', package_id.id if package_id else False),
            ('quantity_product_uom', '>', 0.0),
            ('picked', '=', False),
            ('id', 'not in', tuple(ml_ids_to_ignore)),
        ]

        # We take the current picking first, then the pickings with the latest scheduled date
        def current_picking_first(cand):
            return (
                cand.picking_id != self.move_id.picking_id,
                -(cand.picking_id.scheduled_date or cand.move_id.date).timestamp()
                if cand.picking_id or cand.move_id else 0,
                -cand.id)

        outdated_candidates = self.env['stock.move.line'].search(outdated_move_lines_domain).sorted(current_picking_first)

        # As the move's state is not computed over the move lines, we'll have to manually
        # recompute the moves which we adapted their lines.
        move_to_reassign = self.env['stock.move']
        to_unlink_candidate_ids = set()

        for candidate in outdated_candidates:
            move_to_reassign |= candidate.move_id
            if self.product_uom_id.compare(candidate.quantity_product_uom, quantity) <= 0:
                quantity -= candidate.quantity_product_uom
                to_unlink_candidate_ids.add(candidate.id)
                if self.product_uom_id.is_zero(quantity):
                    break
            else:
                candidate.quantity -= candidate.product_id.uom_id._compute_quantity(quantity, candidate.product_uom_id, rounding_method='HALF-UP')
                break

        move_line_to_unlink = self.env['stock.move.line'].browse(to_unlink_candidate_ids)
        for m in (move_line_to_unlink.move_id | move_to_reassign):
            m.write({
                'procure_method': 'make_to_stock',
                'move_orig_ids': [Command.clear()]
            })
        move_line_to_unlink.unlink()
        move_to_reassign._action_assign()