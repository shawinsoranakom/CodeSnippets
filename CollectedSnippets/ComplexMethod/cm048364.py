def test_40_pack_in_pack(self):
        """ Put a pack in pack"""
        picking_out = self.PickingObj.create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.pack_location.id,
            'state': 'draft',
            'location_dest_id': self.customer_location.id,
        })
        move_out = self.MoveObj.create({
            'product_id': self.productA.id,
            'product_uom_qty': 3,
            'product_uom': self.productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.pack_location.id,
            'location_dest_id': self.customer_location.id,
        })
        picking_pack = self.PickingObj.create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'state': 'draft',
            'location_dest_id': self.pack_location.id,
        })
        move_pack = self.MoveObj.create({
            'product_id': self.productA.id,
            'product_uom_qty': 3,
            'product_uom': self.productA.uom_id.id,
            'picking_id': picking_pack.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.pack_location.id,
            'move_dest_ids': [Command.link(move_out.id)],
        })
        picking_in = self.PickingObj.create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'state': 'draft',
            'location_dest_id': self.stock_location.id,
        })
        move_in = self.MoveObj.create({
            'product_id': self.productA.id,
            'product_uom_qty': 3,
            'product_uom': self.productA.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'move_dest_ids': [Command.link(move_pack.id)],
        })

        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'draft', 'Wrong state of move line.')
        # Confirm incoming shipment.
        picking_in.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # Check incoming shipment move lines state.
        for move in picking_pack.move_ids:
            self.assertEqual(move.state, 'draft', 'Wrong state of move line.')
        # Confirm incoming shipment.
        picking_pack.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_pack.move_ids:
            self.assertEqual(move.state, 'waiting', 'Wrong state of move line.')

        # Check incoming shipment move lines state.
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'draft', 'Wrong state of move line.')
        # Confirm incoming shipment.
        picking_out.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'waiting', 'Wrong state of move line.')

        # Set the quantity done on the pack operation
        move_in.move_line_ids.quantity = 3.0
        # Put in a pack
        picking_in.action_put_in_pack()
        # Get the new package
        picking_in_package = move_in.move_line_ids.result_package_id
        # Validate picking
        picking_in.move_ids.picked = True
        picking_in._action_done()

        # Check first picking state changed to done
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        # Check next picking state changed to 'assigned'
        for move in picking_pack.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # Set the quantity done on the pack operation
        move_pack.move_line_ids.quantity = 3.0
        move_pack.picked = True
        # Get the new package
        picking_pack_package = move_pack.move_line_ids.result_package_id
        # Validate picking
        picking_pack._action_done()

        # Check second picking state changed to done
        for move in picking_pack.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        # Check next picking state changed to 'assigned'
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # Validate picking
        picking_out.move_line_ids.quantity = 3.0
        picking_out_package = move_out.move_line_ids.result_package_id
        picking_out.move_ids.picked = True
        picking_out._action_done()

        # check all pickings are done
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        for move in picking_pack.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')

        # Check picking_in_package is in picking_pack_package
        self.assertEqual(picking_in_package.id, picking_pack_package.id, 'The package created in the picking in is not in the one created in picking pack')
        self.assertEqual(picking_pack_package.id, picking_out_package.id, 'The package created in the picking in is not in the one created in picking pack')
        # Check that we have one quant in customer location.
        quant = self.StockQuantObj.search([
            ('product_id', '=', self.productA.id), ('location_id', '=', self.customer_location.id)
        ])
        self.assertEqual(len(quant), 1, 'There should be one quant with package for customer location')