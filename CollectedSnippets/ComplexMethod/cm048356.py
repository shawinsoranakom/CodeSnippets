def _compute_moves_locations(self):
        for wizard in self:
            if not wizard.picking_id:
                wizard.product_return_moves = [Command.clear()]
                continue
            product_return_moves = [Command.clear()]
            if not wizard.picking_id._can_return():
                raise UserError(_("You may only return Done pickings."))
            # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
            # default values for creation.
            line_fields = list(self.env['stock.return.picking.line']._fields)
            product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
            for move in wizard.picking_id.move_ids:
                if move.state == 'cancel':
                    continue
                if move.location_dest_usage == 'inventory':
                    continue
                product_return_moves_data = dict(product_return_moves_data_tmpl)
                product_return_moves_data.update(wizard._prepare_stock_return_picking_line_vals_from_move(move))
                product_return_moves.append(Command.create(product_return_moves_data))
            if not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
            wizard.product_return_moves = product_return_moves