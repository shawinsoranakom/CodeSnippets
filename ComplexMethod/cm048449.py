def _sanity_check(self, separate_pickings=True):
        """ Sanity check for `button_validate()`
            :param separate_pickings: Indicates if pickings should be checked independently for lot/serial numbers or not.
        """
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        pickings_without_moves = self.filtered(lambda p: not p.move_ids and not p.move_line_ids)
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit')

        no_quantities_done_ids = set()
        pickings_without_quantities = self.env['stock.picking']
        for picking in self:
            has_pick = any(move.picked and move.state not in ('done', 'cancel') for move in picking.move_ids)
            if all(float_is_zero(move.quantity, precision_digits=precision_digits) for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel') and (not has_pick or m.picked))):
                pickings_without_quantities |= picking

        pickings_using_lots = self.filtered(lambda p: p.picking_type_id.use_create_lots or p.picking_type_id.use_existing_lots)
        if pickings_using_lots:
            lines_to_check = pickings_using_lots._get_lot_move_lines_for_sanity_check(no_quantities_done_ids, separate_pickings)
            for line in lines_to_check:
                if not line.lot_name and not line.lot_id:
                    pickings_without_lots |= line.picking_id
                    products_without_lots |= line.product_id

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_("You can’t validate an empty transfer. Please add some products to move before proceeding."))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.', ', '.join(products_without_lots.mapped('display_name'))))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.', ', '.join(pickings_without_moves.mapped('name')))
            if pickings_without_lots:
                message += _(
                    '\n\nTransfers %(transfer_list)s: You need to supply a Lot/Serial number for products %(product_list)s.',
                    transfer_list=pickings_without_lots.mapped('name'),
                    product_list=products_without_lots.mapped('display_name'),
                )
            if message:
                raise UserError(message.lstrip())