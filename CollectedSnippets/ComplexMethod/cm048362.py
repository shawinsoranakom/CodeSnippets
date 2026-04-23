def test_00_picking_create_and_transfer_quantity(self):
        """ Basic stock operation on incoming and outgoing shipment. """
        LotObj = self.env['stock.lot']
        # ----------------------------------------------------------------------
        # Create incoming shipment of product A, B, C, D
        # ----------------------------------------------------------------------
        #   Product A ( 1 Unit ) , Product C ( 10 Unit )
        #   Product B ( 1 Unit ) , Product D ( 10 Unit )
        #   Product D ( 5 Unit )
        # ----------------------------------------------------------------------

        picking_in = self.PickingObj.create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'state': 'draft',
            'location_dest_id': self.stock_location.id,
        })
        move_a = self.MoveObj.create({
            'product_id': self.productA.id,
            'product_uom_qty': 1,
            'product_uom': self.productA.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move_b = self.MoveObj.create({
            'product_id': self.productB.id,
            'product_uom_qty': 1,
            'product_uom': self.productB.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move_c = self.MoveObj.create({
            'product_id': self.productC.id,
            'product_uom_qty': 10,
            'product_uom': self.productC.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move_d = self.MoveObj.create({
            'product_id': self.productD.id,
            'product_uom_qty': 10,
            'product_uom': self.productD.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.productD.id,
            'product_uom_qty': 5,
            'product_uom': self.productD.uom_id.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })

        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'draft', 'Wrong state of move line.')
        # Confirm incoming shipment.
        picking_in.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # ----------------------------------------------------------------------
        # Replace pack operation of incoming shipments.
        # ----------------------------------------------------------------------
        picking_in.action_assign()
        move_a.move_line_ids.quantity = 4
        move_b.move_line_ids.quantity = 5
        move_c.move_line_ids.quantity = 5
        move_d.move_line_ids.quantity = 5
        (move_a | move_b | move_c | move_d).picked = True
        lot2_productC = LotObj.create({'name': 'C Lot 2', 'product_id': self.productC.id})
        self.StockPackObj.create({
            'product_id': self.productC.id,
            'quantity': 2,
            'product_uom_id': self.productC.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'move_id': move_c.id,
            'lot_id': lot2_productC.id,
        })
        self.StockPackObj.create({
            'product_id': self.productD.id,
            'quantity': 2,
            'product_uom_id': self.productD.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'move_id': move_d.id
        })

        # Check incoming shipment total quantity of pack operation
        total_qty = sum(self.StockPackObj.search([('move_id', 'in', picking_in.move_ids.ids)]).mapped('quantity'))
        self.assertEqual(total_qty, 23, 'Wrong quantity in pack operation')

        # Transfer Incoming Shipment.
        picking_in._action_done()

        # ----------------------------------------------------------------------
        # Check state, quantity and total moves of incoming shipment.
        # ----------------------------------------------------------------------

        # Check total no of move lines of incoming shipment. move line e disappear from original picking to go in backorder.
        self.assertEqual(len(picking_in.move_ids), 4, 'Wrong number of move lines.')
        # Check incoming shipment state.
        self.assertEqual(picking_in.state, 'done', 'Incoming shipment state should be done.')
        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        # Check product A done quantity must be 3 and 1
        moves = self.MoveObj.search([('product_id', '=', self.productA.id), ('picking_id', '=', picking_in.id)])
        self.assertEqual(moves.quantity, 4.0, 'Wrong move quantity for product A.')
        # Check product B done quantity must be 4 and 1
        moves = self.MoveObj.search([('product_id', '=', self.productB.id), ('picking_id', '=', picking_in.id)])
        self.assertEqual(moves.quantity, 5.0, 'Wrong move quantity for product B.')
        # Check product C done quantity must be 7
        c_done_qty = self.MoveObj.search([('product_id', '=', self.productC.id), ('picking_id', '=', picking_in.id)], limit=1).product_uom_qty
        self.assertEqual(c_done_qty, 7.0, 'Wrong move quantity of product C (%s found instead of 7)' % (c_done_qty))
        # Check product D done quantity must be 7
        d_done_qty = self.MoveObj.search([('product_id', '=', self.productD.id), ('picking_id', '=', picking_in.id)], limit=1).product_uom_qty
        self.assertEqual(d_done_qty, 7.0, 'Wrong move quantity of product D (%s found instead of 7)' % (d_done_qty))

        # ----------------------------------------------------------------------
        # Check Back order of Incoming shipment.
        # ----------------------------------------------------------------------

        # Check back order created or not.
        back_order_in = self.PickingObj.search([('backorder_id', '=', picking_in.id)])
        self.assertEqual(len(back_order_in), 1, 'Back order should be created.')
        # Check total move lines of back order.
        self.assertEqual(len(back_order_in.move_ids), 2, 'Wrong number of move lines.')
        # Check back order should be created with 3 quantity of product C.
        moves = self.MoveObj.search([('product_id', '=', self.productC.id), ('picking_id', '=', back_order_in.id)])
        product_c_qty = [move.product_uom_qty for move in moves]
        self.assertEqual(sum(product_c_qty), 3.0, 'Wrong move quantity of product C (%s found instead of 3)' % (product_c_qty))
        # Check back order should be created with 8 quantity of product D.
        moves = self.MoveObj.search([('product_id', '=', self.productD.id), ('picking_id', '=', back_order_in.id)])
        product_d_qty = [move.product_uom_qty for move in moves]
        self.assertEqual(sum(product_d_qty), 8.0, 'Wrong move quantity of product D (%s found instead of 8)' % (product_d_qty))

        # ======================================================================
        # Create Outgoing shipment with ...
        #   product A ( 10 Unit ) , product B ( 5 Unit )
        #   product C (  3 unit ) , product D ( 10 Unit )
        # ======================================================================

        picking_out = self.PickingObj.create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'state': 'draft',
            'location_dest_id': self.customer_location.id,
        })
        move_cust_a = self.MoveObj.create({
            'product_id': self.productA.id,
            'product_uom_qty': 10,
            'product_uom': self.productA.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        move_cust_b = self.MoveObj.create({
            'product_id': self.productB.id,
            'product_uom_qty': 5,
            'product_uom': self.productB.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        move_cust_c = self.MoveObj.create({
            'product_id': self.productC.id,
            'product_uom_qty': 3,
            'product_uom': self.productC.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        move_cust_d = self.MoveObj.create({
            'product_id': self.productD.id,
            'product_uom_qty': 10,
            'product_uom': self.productD.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        # Confirm outgoing shipment.
        picking_out.action_confirm()
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'confirmed', 'Wrong state of move line.')
        # Product assign to outgoing shipments
        picking_out.action_assign()
        self.assertEqual(move_cust_a.state, 'partially_available', 'Wrong state of move line.')
        self.assertEqual(move_cust_b.state, 'assigned', 'Wrong state of move line.')
        self.assertEqual(move_cust_c.state, 'assigned', 'Wrong state of move line.')
        self.assertEqual(move_cust_d.state, 'partially_available', 'Wrong state of move line.')
        # Check availability for product A
        aval_a_qty = self.MoveObj.search([('product_id', '=', self.productA.id), ('picking_id', '=', picking_out.id)], limit=1).quantity
        self.assertEqual(aval_a_qty, 4.0, 'Wrong move quantity availability of product A (%s found instead of 4)' % (aval_a_qty))
        # Check availability for product B
        aval_b_qty = self.MoveObj.search([('product_id', '=', self.productB.id), ('picking_id', '=', picking_out.id)], limit=1).quantity
        self.assertEqual(aval_b_qty, 5.0, 'Wrong move quantity availability of product B (%s found instead of 5)' % (aval_b_qty))
        # Check availability for product C
        aval_c_qty = self.MoveObj.search([('product_id', '=', self.productC.id), ('picking_id', '=', picking_out.id)], limit=1).quantity
        self.assertEqual(aval_c_qty, 3.0, 'Wrong move quantity availability of product C (%s found instead of 3)' % (aval_c_qty))
        # Check availability for product D
        aval_d_qty = self.MoveObj.search([('product_id', '=', self.productD.id), ('picking_id', '=', picking_out.id)], limit=1).quantity
        self.assertEqual(aval_d_qty, 7.0, 'Wrong move quantity availability of product D (%s found instead of 7)' % (aval_d_qty))

        # ----------------------------------------------------------------------
        # Replace pack operation of outgoing shipment.
        # ----------------------------------------------------------------------

        move_cust_a.move_line_ids.quantity = 2.0
        move_cust_b.move_line_ids.quantity = 3.0
        self.StockPackObj.create({
            'product_id': self.productB.id,
            'quantity': 2,
            'product_uom_id': self.productB.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'move_id': move_cust_b.id})
        # TODO care if product_qty and lot_id are set at the same times the system do 2 unreserve.
        move_cust_c.move_line_ids[0].write({
            'quantity': 2.0,
            'lot_id': lot2_productC.id,
        })
        move_cust_c.move_line_ids[1].write({
            'quantity': 3.0,
        })
        move_cust_d.move_line_ids.quantity = 6.0

        # Transfer picking.
        (move_cust_a | move_cust_b | move_cust_c | move_cust_d).picked = True
        picking_out._action_done()

        # ----------------------------------------------------------------------
        # Check state, quantity and total moves of outgoing shipment.
        # ----------------------------------------------------------------------

        # check outgoing shipment status.
        self.assertEqual(picking_out.state, 'done', 'Wrong state of outgoing shipment.')
        # check outgoing shipment total moves and and its state.
        self.assertEqual(len(picking_out.move_ids), 4, 'Wrong number of move lines')
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        back_order_out = self.PickingObj.search([('backorder_id', '=', picking_out.id)])

        # ------------------
        # Check back order.
        # -----------------

        self.assertEqual(len(back_order_out), 1, 'Back order should be created.')
        # Check total move lines of back order.
        self.assertEqual(len(back_order_out.move_ids), 2, 'Wrong number of move lines')
        # Check back order should be created with 8 quantity of product A.
        product_a_qty = self.MoveObj.search([('product_id', '=', self.productA.id), ('picking_id', '=', back_order_out.id)], limit=1).product_uom_qty
        self.assertEqual(product_a_qty, 8.0, 'Wrong move quantity of product A (%s found instead of 8)' % (product_a_qty))
        # Check back order should be created with 4 quantity of product D.
        product_d_qty = self.MoveObj.search([('product_id', '=', self.productD.id), ('picking_id', '=', back_order_out.id)], limit=1).product_uom_qty
        self.assertEqual(product_d_qty, 4.0, 'Wrong move quantity of product D (%s found instead of 4)' % (product_d_qty))

        # -----------------------------------------------------------------------
        # Check stock location quant quantity and quantity available
        # of product A, B, C, D
        # -----------------------------------------------------------------------

        # Check quants and available quantity for product A
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]

        self.assertEqual(sum(total_qty), 2.0, 'Expecting 2.0 Unit , got %.4f Unit on location stock!' % (sum(total_qty)))
        self.assertEqual(self.productA.qty_available, 2.0, 'Wrong quantity available (%s found instead of 2.0)' % (self.productA.qty_available))
        # Check quants and available quantity for product B
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productB.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        self.assertFalse(quants, 'No quant should found as outgoing shipment took everything out of stock.')
        self.assertEqual(self.productB.qty_available, 0.0, 'Product B should have zero quantity available.')
        # Check quants and available quantity for product C
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productC.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 2.0, 'Expecting 2.0 Unit, got %.4f Unit on location stock!' % (sum(total_qty)))
        self.assertEqual(self.productC.qty_available, 2.0, 'Wrong quantity available (%s found instead of 2.0)' % (self.productC.qty_available))
        # Check quants and available quantity for product D
        quant = self.StockQuantObj.search([
            ('product_id', '=', self.productD.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ], limit=1)
        self.assertEqual(quant.quantity, 1.0, 'Expecting 1.0 Unit , got %.4f Unit on location stock!' % (quant.quantity))
        self.assertEqual(self.productD.qty_available, 1.0, 'Wrong quantity available (%s found instead of 1.0)' % (self.productD.qty_available))

        # -----------------------------------------------------------------------
        # Back Order of Incoming shipment
        # -----------------------------------------------------------------------

        lot3_productC = LotObj.create({'name': 'Lot 3', 'product_id': self.productC.id})
        lot4_productC = LotObj.create({'name': 'Lot 4', 'product_id': self.productC.id})
        lot5_productC = LotObj.create({'name': 'Lot 5', 'product_id': self.productC.id})
        lot6_productC = LotObj.create({'name': 'Lot 6', 'product_id': self.productC.id})
        lot1_productD = LotObj.create({'name': 'Lot 1', 'product_id': self.productD.id})
        LotObj.create({'name': 'Lot 2', 'product_id': self.productD.id})

        # Confirm back order of incoming shipment.
        back_order_in.action_confirm()
        self.assertEqual(back_order_in.state, 'assigned', 'Wrong state of incoming shipment back order: %s instead of %s' % (back_order_in.state, 'assigned'))
        for move in back_order_in.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # ----------------------------------------------------------------------
        # Replace pack operation (Back order of Incoming shipment)
        # ----------------------------------------------------------------------

        packD = self.StockPackObj.search([('product_id', '=', self.productD.id), ('picking_id', '=', back_order_in.id)], order='quantity')
        self.assertEqual(len(packD), 1, 'Wrong number of pack operation.')
        packD[0].write({
            'quantity': 8,
            'lot_id': lot1_productD.id,
        })
        packCs = self.StockPackObj.search([('product_id', '=', self.productC.id), ('picking_id', '=', back_order_in.id)], limit=1)
        packCs.write({
            'quantity': 1,
            'lot_id': lot3_productC.id,
        })
        self.StockPackObj.create({
            'product_id': self.productC.id,
            'quantity': 1,
            'product_uom_id': self.productC.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_id': back_order_in.id,
            'lot_id': lot4_productC.id,
        })
        self.StockPackObj.create({
            'product_id': self.productC.id,
            'quantity': 2,
            'product_uom_id': self.productC.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_id': back_order_in.id,
            'lot_id': lot5_productC.id,
        })
        self.StockPackObj.create({
            'product_id': self.productC.id,
            'quantity': 2,
            'product_uom_id': self.productC.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_id': back_order_in.id,
            'lot_id': lot6_productC.id,
        })
        self.StockPackObj.create({
            'product_id': self.productA.id,
            'quantity': 10,
            'product_uom_id': self.productA.uom_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_id': back_order_in.id
        })
        back_order_in.move_ids.picked = True
        back_order_in._action_done()

        # ----------------------------------------------------------------------
        # Check state, quantity and total moves (Back order of Incoming shipment).
        # ----------------------------------------------------------------------

        # Check total no of move lines.
        self.assertEqual(len(back_order_in.move_ids), 3, 'Wrong number of move lines')
        # Check incoming shipment state must be 'Done'.
        self.assertEqual(back_order_in.state, 'done', 'Wrong state of picking.')
        # Check incoming shipment move lines state must be 'Done'.
        for move in back_order_in.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move lines.')
        # Check product A done quantity must be 10
        movesA = self.MoveObj.search([('product_id', '=', self.productA.id), ('picking_id', '=', back_order_in.id)])
        self.assertEqual(movesA.quantity, 10, "Wrong move quantity of product A (%s found instead of 10)" % (movesA.quantity))
        # Check product C done quantity must be 3.0, 1.0, 2.0
        movesC = self.MoveObj.search([('product_id', '=', self.productC.id), ('picking_id', '=', back_order_in.id)])
        self.assertEqual(movesC.quantity, 6.0, 'Wrong quantity of moves product C.')
        # Check product D done quantity must be 5.0 and 3.0
        movesD = self.MoveObj.search([('product_id', '=', self.productD.id), ('picking_id', '=', back_order_in.id)])
        d_done_qty = [move.quantity for move in movesD]
        self.assertEqual(set(d_done_qty), set([8.0]), 'Wrong quantity of moves product D.')
        # Check no back order is created.
        self.assertFalse(self.PickingObj.search([('backorder_id', '=', back_order_in.id)]), "Should not create any back order.")

        # -----------------------------------------------------------------------
        # Check stock location quant quantity and quantity available
        # of product A, B, C, D
        # -----------------------------------------------------------------------

        # Check quants and available quantity for product A.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productA.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 12.0, 'Wrong total stock location quantity (%s found instead of 12)' % (sum(total_qty)))
        self.assertEqual(self.productA.qty_available, 12.0, 'Wrong quantity available (%s found instead of 12)' % (self.productA.qty_available))
        # Check quants and available quantity for product B.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productB.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        self.assertFalse(quants, 'No quant should found as outgoing shipment took everything out of stock')
        self.assertEqual(self.productB.qty_available, 0.0, 'Total quantity in stock should be 0 as the backorder took everything out of stock')
        # Check quants and available quantity for product C.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productC.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 8.0, 'Wrong total stock location quantity (%s found instead of 8)' % (sum(total_qty)))
        self.assertEqual(self.productC.qty_available, 8.0, 'Wrong quantity available (%s found instead of 8)' % (self.productC.qty_available))
        # Check quants and available quantity for product D.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productD.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 9.0, 'Wrong total stock location quantity (%s found instead of 9)' % (sum(total_qty)))
        self.assertEqual(self.productD.qty_available, 9.0, 'Wrong quantity available (%s found instead of 9)' % (self.productD.qty_available))

        # -----------------------------------------------------------------------
        # Back order of Outgoing shipment
        # ----------------------------------------------------------------------

        back_order_out._action_done()

        # Check stock location quants and available quantity for product A.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.productA.id), ('location_id', '=', self.stock_location.id), ('quantity', '!=', 0)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertGreaterEqual(float_round(sum(total_qty), precision_rounding=0.0001), 1, 'Total stock location quantity for product A should not be nagative.')