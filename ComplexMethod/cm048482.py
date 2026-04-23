def _action_done(self, cancel_backorder=False):
        moves = self.filtered(
            lambda move: move.state == 'draft')._action_confirm(merge=False)
        moves = (self | moves).exists().filtered(lambda x: x.state not in ('done', 'cancel'))

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        ml_ids_to_unlink = OrderedSet()
        for move in moves:
            if move.picked:
                # in theory, we should only have a mix of picked and non-picked mls in the barcode use case
                # where non-scanned mls = not picked => we definitely don't want to validate them
                ml_ids_to_unlink |= move.move_line_ids.filtered(lambda ml: not ml.picked).ids
            if (move.quantity <= 0 or not move.picked) and not move.is_inventory:
                if move.product_uom.compare(move.product_uom_qty, 0.0) == 0 or cancel_backorder:
                    move._action_cancel()
        self.env['stock.move.line'].browse(ml_ids_to_unlink).unlink()

        moves_todo = moves.filtered(lambda m:
            not (m.state == 'cancel' or (m.quantity <= 0 and not m.is_inventory) or not m.picked)
        )

        moves_todo._check_company()
        if not cancel_backorder:
            moves_todo._create_backorder()
        moves_todo.mapped('move_line_ids').sorted()._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .move_line_ids.filtered(lambda ml: ml.picked).mapped('result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(lambda q: q.product_uom_id.compare(q.quantity, 0.0) > 0).mapped('location_id')) > 1:
                error_msg = _(
                    'You cannot move the same package content more than once in the same transfer'
                    ' or split the same package into two location.'
                )
                package_msg = _("\nPackage: %s", result_package.name)
                raise UserError(error_msg + package_msg)
        if any(ml.package_id and ml.package_id == ml.result_package_id for ml in moves_todo.move_line_ids):
            self.env['stock.quant']._unlink_zero_quants()
        picking = moves_todo.mapped('picking_id')
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})

        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])

        # Break move dest link if move dest and move_dest source are not the same,
        # so that when move_dests._action_assign is called, the move lines are not created with
        # the new location, they should not be created at all.
        moves_to_push = moves_todo.filtered(lambda m: not m._skip_push())
        if moves_to_push:
            moves_to_push._push_apply()
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_company(company_id)._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves

        if picking and not cancel_backorder:
            backorder = picking._create_backorder()
            if any([m.state == 'assigned' for m in backorder.move_ids]):
                backorder._check_entire_pack()
        if moves_todo:
            moves_todo._check_quantity()
            moves_todo._action_synch_order()
        return moves_todo