def _make_in_move(self,
            product,
            quantity,
            unit_cost=None,
            create_picking=False,
            company=None,
            **kwargs,
        ):
        """ Helper to create and validate a receipt move.

        :param product: Product to move
        :param quantity: Quantity to move
        :param unit_cost: Price unit
        :param create_picking: Create the picking containing the created move
        :param company: If set, the move is created in that company's context
            and warehouse defaults are resolved from that company's warehouse.
        :param **kwargs: stock.move fields that you can override
            ''location_id: origin location for the move
            ''location_dest_id: destination location for the move
            ''lot_ids: list of lot (split among the quantity)
            ''picking_type_id: picking type
            ''uom_id: Unit of measure
            ''owner_id: Consignment owner
        """
        env = self.env['stock.move'].with_company(company).env if company else self.env
        if company:
            warehouse = env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
            default_dest = warehouse.lot_stock_id.id
            default_picking_type = warehouse.in_type_id.id
        else:
            default_dest = self.stock_location.id
            default_picking_type = self.picking_type_in.id

        product_qty = quantity
        if kwargs.get('uom_id'):
            uom = self.env['uom.uom'].browse(kwargs.get('uom_id'))
            product_qty = uom._compute_quantity(quantity, product.uom_id)
        move_vals = {
            'product_id': product.id,
            'location_id': kwargs.get('location_id', self.supplier_location.id),
            'location_dest_id': kwargs.get('location_dest_id', default_dest),
            'product_uom': kwargs.get('uom_id', self.uom.id),
            'product_uom_qty': quantity,
            'picking_type_id': kwargs.get('picking_type_id', default_picking_type),
        }
        if unit_cost:
            move_vals['value_manual'] = unit_cost * product_qty
            move_vals['price_unit'] = unit_cost
        else:
            move_vals['value_manual'] = product.standard_price * product_qty
        in_move = env['stock.move'].create(move_vals)

        if create_picking:
            picking = env['stock.picking'].create({
                'picking_type_id': in_move.picking_type_id.id,
                'location_id': in_move.location_id.id,
                'location_dest_id': in_move.location_dest_id.id,
                'owner_id': kwargs.get('owner_id', False),
                'partner_id': kwargs.get('partner_id', False),
                })
            in_move.picking_id = picking.id

        in_move._action_confirm()
        lot_ids = kwargs.get('lot_ids')
        if lot_ids:
            in_move.move_line_ids.unlink()
            in_move.move_line_ids = [Command.create({
                'location_id': self.supplier_location.id,
                'location_dest_id': in_move.location_dest_id.id,
                'quantity': quantity / len(lot_ids),
                'product_id': product.id,
                'lot_id': lot.id,
            }) for lot in lot_ids]
        else:
            in_move._action_assign()

        if not create_picking and kwargs.get('owner_id'):
            in_move.move_line_ids.owner_id = kwargs.get('owner_id')

        in_move.picked = True
        if create_picking:
            picking.button_validate()
        else:
            in_move._action_done()

        return in_move