def _apply_inventory(self, date=None):
        # Consider the inventory_quantity as set => recompute the inventory_diff_quantity if needed
        self.inventory_quantity_set = True
        move_vals = []
        default_loss_locations = {}
        quants_with_missing_loss_locations = self.filtered(lambda quant: not quant.product_id.with_company(quant.company_id).property_stock_inventory)
        if quants_with_missing_loss_locations:
            for company in quants_with_missing_loss_locations.mapped('company_id'):
                loss_location_id = self.env['ir.default'].with_company(company)._get_model_defaults(
                    'product.template').get('property_stock_inventory')
                default_loss_locations[company.id] = self.env['stock.location'].browse(loss_location_id)
        for quant in self:
            # if inventory applied from product's inverse_qty and the inventory_diff_quantity is 0,
            # we skip creating a move with 0 quantity.
            if quant.env.context.get('from_inverse_qty') and quant.product_uom_id.compare(quant.inventory_diff_quantity, 0) == 0:
                continue
            inventory_location = quant.product_id.with_company(quant.company_id).property_stock_inventory or\
                default_loss_locations.get(quant.company_id.id)
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if quant.product_uom_id.compare(quant.inventory_diff_quantity, 0) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     inventory_location,
                                                     quant.location_id, package_dest_id=quant.package_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     inventory_location,
                                                     package_id=quant.package_id))
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
        moves.with_context(ignore_dest_packages=True)._action_done()
        if date:
            moves.date = date
        moves._trigger_assign()
        self.location_id.sudo().write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]
        self.action_clear_inventory_quantity()