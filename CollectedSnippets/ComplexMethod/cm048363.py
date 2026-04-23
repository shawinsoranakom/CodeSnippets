def test_10_pickings_transfer_with_different_uom(self):
        """ Picking transfer with diffrent unit of meassure. """

        # ----------------------------------------------------------------------
        # Create incoming shipment of products DozA, SDozA, kgB, gB
        # ----------------------------------------------------------------------
        #   DozA ( 10 Dozen ) , SDozA ( 10.5 SuperDozen )
        #   kgB ( 0.020 kg ),gB ( 525.3 g )
        # ----------------------------------------------------------------------

        picking_in_A = self.PickingObj.create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'state': 'draft',
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.DozA.id,
            'product_uom_qty': 10,
            'product_uom': self.DozA.uom_id.id,
            'picking_id': picking_in_A.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.SDozA.id,
            'product_uom_qty': 10.5,
            'product_uom': self.SDozA.uom_id.id,
            'picking_id': picking_in_A.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.kgB.id,
            'product_uom_qty': 0.020,
            'product_uom': self.kgB.uom_id.id,
            'picking_id': picking_in_A.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.gB.id,
            'product_uom_qty': 525.3,
            'product_uom': self.gB.uom_id.id,
            'picking_id': picking_in_A.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })

        # Check incoming shipment move lines state.
        for move in picking_in_A.move_ids:
            self.assertEqual(move.state, 'draft', 'Move state must be draft.')
        # Confirm incoming shipment.
        picking_in_A.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_in_A.move_ids:
            self.assertEqual(move.state, 'assigned', 'Move state must be draft.')
        picking_in_A.button_validate()

        # -----------------------------------------------------------------------
        # Check stock location quant quantity and quantity available
        # -----------------------------------------------------------------------

        # Check quants and available quantity for product DozA
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.DozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 10, 'Expecting 10 Dozen , got %.4f Dozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.DozA.qty_available, 10, 'Wrong quantity available (%s found instead of 10)' % (self.DozA.qty_available))
        # Check quants and available quantity for product SDozA
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.SDozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 10.5, 'Expecting 10.5 SDozen , got %.4f SDozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.SDozA.qty_available, 10.5, 'Wrong quantity available (%s found instead of 10.5)' % (self.SDozA.qty_available))
        # Check quants and available quantity for product gB
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.gB.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertAlmostEqual(sum(total_qty), 525.3, msg='Expecting 525.3 gram , got %.4f gram on location stock!' % (sum(total_qty)))
        self.assertAlmostEqual(self.gB.qty_available, 525.3, msg='Wrong quantity available (%s found instead of 525.3' % (self.gB.qty_available))
        # Check quants and available quantity for product kgB
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.kgB.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 0.020, 'Expecting 0.020 kg , got %.4f kg on location stock!' % (sum(total_qty)))
        self.assertEqual(self.kgB.qty_available, 0.020, 'Wrong quantity available (%s found instead of 0.020)' % (self.kgB.qty_available))

        # ----------------------------------------------------------------------
        # Create Incoming Shipment B
        # ----------------------------------------------------------------------

        picking_in_B = self.PickingObj.create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'state': 'draft',
            'location_dest_id': self.stock_location.id,
        })
        move_in_a = self.MoveObj.create({
            'product_id': self.DozA.id,
            'product_uom_qty': 120,
            'product_uom': self.uom_unit.id,
            'picking_id': picking_in_B.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.SDozA.id,
            'product_uom_qty': 1512,
            'product_uom': self.uom_unit.id,
            'picking_id': picking_in_B.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.kgB.id,
            'product_uom_qty': 20.0,
            'product_uom': self.uom_gm.id,
            'picking_id': picking_in_B.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': self.gB.id,
            'product_uom_qty': 0.525,
            'product_uom': self.uom_kg.id,
            'picking_id': picking_in_B.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })

        # Check incoming shipment move lines state.
        for move in picking_in_B.move_ids:
            self.assertEqual(move.state, 'draft', 'Wrong state of move line.')
        # Confirm incoming shipment.
        picking_in_B.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_in_B.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')

        # ----------------------------------------------------------------------
        # Check product quantity and unit of measure of pack operaation.
        # ----------------------------------------------------------------------

        # Check pack operation quantity and unit of measure for product DozA.
        PackdozA = self.StockPackObj.search([('product_id', '=', self.DozA.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(PackdozA.quantity, 120, 'Wrong quantity in pack operation (%s found instead of 120)' % (PackdozA.quantity))
        self.assertEqual(PackdozA.quantity_product_uom, 10, 'Wrong real quantity in pack operation (%s found instead of 10)' % (PackdozA.quantity_product_uom))
        self.assertEqual(PackdozA.product_uom_id.id, self.uom_unit.id, 'Wrong uom in pack operation for product DozA.')
        # Check pack operation quantity and unit of measure for product SDozA.
        PackSdozA = self.StockPackObj.search([('product_id', '=', self.SDozA.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(PackSdozA.quantity, 1512, 'Wrong quantity in pack operation (%s found instead of 1512)' % (PackSdozA.quantity))
        self.assertEqual(PackSdozA.product_uom_id.id, self.uom_unit.id, 'Wrong uom in pack operation for product SDozA.')
        # Check pack operation quantity and unit of measure for product gB.
        packgB = self.StockPackObj.search([('product_id', '=', self.gB.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(packgB.quantity, 0.525, 'Wrong quantity in pack operation (%s found instead of 0.525)' % (packgB.quantity))
        self.assertEqual(packgB.quantity_product_uom, 525, 'Wrong real quantity in pack operation (%s found instead of 525)' % (packgB.quantity_product_uom))
        self.assertEqual(packgB.product_uom_id.id, packgB.move_id.product_uom.id, 'Wrong uom in pack operation for product kgB.')
        # Check pack operation quantity and unit of measure for product kgB.
        packkgB = self.StockPackObj.search([('product_id', '=', self.kgB.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(packkgB.quantity, 20.0, 'Wrong quantity in pack operation (%s found instead of 20)' % (packkgB.quantity))
        self.assertEqual(packkgB.product_uom_id.id, self.uom_gm.id, 'Wrong uom in pack operation for product kgB')

        # ----------------------------------------------------------------------
        # Replace pack operation of incoming shipment.
        # ----------------------------------------------------------------------

        self.StockPackObj.search([('product_id', '=', self.kgB.id), ('picking_id', '=', picking_in_B.id)]).write({
            'quantity': 0.020, 'product_uom_id': self.uom_kg.id})
        self.StockPackObj.search([('product_id', '=', self.gB.id), ('picking_id', '=', picking_in_B.id)]).write({
            'quantity': 526, 'product_uom_id': self.uom_gm.id})
        self.StockPackObj.search([('product_id', '=', self.DozA.id), ('picking_id', '=', picking_in_B.id)]).write({
            'quantity': 4, 'product_uom_id': self.uom_dozen.id})
        self.StockPackObj.create({
            'product_id': self.DozA.id,
            'quantity': 48,
            'product_uom_id': self.uom_unit.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'move_id': move_in_a.id
        })

        # -----------------
        # Transfer product.
        # -----------------

        res_dict_for_back_order = picking_in_B.button_validate()
        backorder_wizard = self.env[(res_dict_for_back_order.get('res_model'))].browse(res_dict_for_back_order.get('res_id')).with_context(res_dict_for_back_order['context'])
        backorder_wizard.process()

        # -----------------------------------------------------------------------
        # Check incoming shipment
        # -----------------------------------------------------------------------
        # Check incoming shipment state.
        self.assertEqual(picking_in_B.state, 'done', 'Incoming shipment state should be done.')
        # Check incoming shipment move lines state.
        for move in picking_in_B.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move line.')
        # Check total done move lines for incoming shipment.
        self.assertEqual(len(picking_in_B.move_ids), 4, 'Wrong number of move lines')
        # Check product DozA done quantity.
        moves_DozA = self.MoveObj.search([('product_id', '=', self.DozA.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(moves_DozA.quantity, 96, 'Wrong move quantity (%s found instead of 96)' % (moves_DozA.product_uom_qty))
        self.assertEqual(moves_DozA.product_uom.id, self.uom_unit.id, 'Wrong uom in move for product DozA.')
        # Check product SDozA done quantity.
        moves_SDozA = self.MoveObj.search([('product_id', '=', self.SDozA.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(moves_SDozA.quantity, 1512, 'Wrong move quantity (%s found instead of 1512)' % (moves_SDozA.product_uom_qty))
        self.assertEqual(moves_SDozA.product_uom.id, self.uom_unit.id, 'Wrong uom in move for product SDozA.')
        # Check product kgB done quantity.
        moves_kgB = self.MoveObj.search([('product_id', '=', self.kgB.id), ('picking_id', '=', picking_in_B.id)], limit=1)
        self.assertEqual(moves_kgB.quantity, 20, 'Wrong quantity in move (%s found instead of 20)' % (moves_kgB.product_uom_qty))
        self.assertEqual(moves_kgB.product_uom.id, self.uom_gm.id, 'Wrong uom in move for product kgB.')
        # Check two moves created for product gB with quantity (0.525 kg and 0.3 g)
        moves_gB_kg = self.MoveObj.search([('product_id', '=', self.gB.id), ('picking_id', '=', picking_in_B.id), ('product_uom', '=', self.uom_kg.id)], limit=1)
        self.assertEqual(moves_gB_kg.quantity, 0.526, 'Wrong move quantity (%s found instead of 0.526)' % (moves_gB_kg.product_uom_qty))
        self.assertEqual(moves_gB_kg.product_uom.id, self.uom_kg.id, 'Wrong uom in move for product gB.')

        # TODO Test extra move once the uom is editable in the move_lines

        # ----------------------------------------------------------------------
        # Check Back order of Incoming shipment.
        # ----------------------------------------------------------------------

        # Check back order created or not.
        bo_in_B = self.PickingObj.search([('backorder_id', '=', picking_in_B.id)])
        self.assertEqual(len(bo_in_B), 1, 'Back order should be created.')

        # Assigned user should not be copied
        self.assertTrue(picking_in_B.user_id)
        self.assertFalse(bo_in_B.user_id)

        # Check total move lines of back order.
        self.assertEqual(len(bo_in_B.move_ids), 1, 'Wrong number of move lines')
        # Check back order created with correct quantity and uom or not.
        moves_DozA = self.MoveObj.search([('product_id', '=', self.DozA.id), ('picking_id', '=', bo_in_B.id)], limit=1)
        self.assertEqual(moves_DozA.product_uom_qty, 24.0, 'Wrong move quantity (%s found instead of 0.525)' % (moves_DozA.product_uom_qty))
        self.assertEqual(moves_DozA.product_uom.id, self.uom_unit.id, 'Wrong uom in move for product DozA.')

        # ----------------------------------------------------------------------
        # Check product stock location quantity and quantity available.
        # ----------------------------------------------------------------------

        # Check quants and available quantity for product DozA
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.DozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 18, 'Expecting 18 Dozen , got %.4f Dozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.DozA.qty_available, 18, 'Wrong quantity available (%s found instead of 18)' % (self.DozA.qty_available))
        # Check quants and available quantity for product SDozA
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.SDozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 21, 'Expecting 21 SDozen , got %.4f SDozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.SDozA.qty_available, 21, 'Wrong quantity available (%s found instead of 21)' % (self.SDozA.qty_available))
        # Check quants and available quantity for product gB.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.gB.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(round(sum(total_qty), 1), 1051.3, 'Expecting 1051 Gram , got %.4f Gram on location stock!' % (sum(total_qty)))
        self.assertEqual(round(self.gB.qty_available, 1), 1051.3, 'Wrong quantity available (%s found instead of 1051)' % (self.gB.qty_available))
        # Check quants and available quantity for product kgB.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.kgB.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 0.040, 'Expecting 0.040 kg , got %.4f kg on location stock!' % (sum(total_qty)))
        self.assertEqual(self.kgB.qty_available, 0.040, 'Wrong quantity available (%s found instead of 0.040)' % (self.kgB.qty_available))

        # ----------------------------------------------------------------------
        # Create outgoing shipment.
        # ----------------------------------------------------------------------

        before_out_quantity = self.kgB.qty_available
        picking_out = self.PickingObj.create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'state': 'draft',
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': self.kgB.id,
            'product_uom_qty': 0.966,
            'product_uom': self.uom_gm.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': self.kgB.id,
            'product_uom_qty': 0.034,
            'product_uom': self.uom_gm.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        picking_out.action_confirm()
        picking_out.action_assign()
        picking_out.button_validate()

        # Check quantity difference after stock transfer.
        quantity_diff = before_out_quantity - self.kgB.qty_available
        self.assertEqual(float_round(quantity_diff, precision_rounding=0.0001), 0.001, 'Wrong quantity difference.')
        self.assertEqual(self.kgB.qty_available, 0.039, 'Wrong quantity available (%s found instead of 0.039)' % (self.kgB.qty_available))

        # ======================================================================
        # Outgoing shipments.
        # ======================================================================

        # Create Outgoing shipment with ...
        #   product DozA ( 54 Unit ) , SDozA ( 288 Unit )
        #   product gB ( 0.503 kg ), product kgB (  19 g )
        # ======================================================================

        picking_out = self.PickingObj.create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'state': 'draft',
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': self.DozA.id,
            'product_uom_qty': 54,
            'product_uom': self.uom_unit.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': self.SDozA.id,
            'product_uom_qty': 288,
            'product_uom': self.uom_unit.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': self.gB.id,
            'product_uom_qty': 0.503,
            'product_uom': self.uom_kg.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': self.kgB.id,
            'product_uom_qty': 20,
            'product_uom': self.uom_gm.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        # Confirm outgoing shipment.
        picking_out.action_confirm()
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'confirmed', 'Wrong state of move line.')
        # Assing product to outgoing shipments
        picking_out.action_assign()
        for move in picking_out.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')
        # Check product A available quantity
        DozA_qty = self.MoveObj.search([('product_id', '=', self.DozA.id), ('picking_id', '=', picking_out.id)], limit=1).product_qty
        self.assertEqual(DozA_qty, 4.5, 'Wrong move quantity availability (%s found instead of 4.5)' % (DozA_qty))
        # Check product B available quantity
        SDozA_qty = self.MoveObj.search([('product_id', '=', self.SDozA.id), ('picking_id', '=', picking_out.id)], limit=1).product_qty
        self.assertEqual(SDozA_qty, 2, 'Wrong move quantity availability (%s found instead of 2)' % (SDozA_qty))
        # Check product D available quantity
        gB_qty = self.MoveObj.search([('product_id', '=', self.gB.id), ('picking_id', '=', picking_out.id)], limit=1).product_qty
        self.assertEqual(gB_qty, 503, 'Wrong move quantity availability (%s found instead of 503)' % (gB_qty))
        # Check product D available quantity
        kgB_qty = self.MoveObj.search([('product_id', '=', self.kgB.id), ('picking_id', '=', picking_out.id)], limit=1).product_qty
        self.assertEqual(kgB_qty, 0.020, 'Wrong move quantity availability (%s found instead of 0.020)' % (kgB_qty))

        picking_out.button_validate()
        # ----------------------------------------------------------------------
        # Check product stock location quantity and quantity available.
        # ----------------------------------------------------------------------

        # Check quants and available quantity for product DozA
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.DozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 13.5, 'Expecting 13.5 Dozen , got %.4f Dozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.DozA.qty_available, 13.5, 'Wrong quantity available (%s found instead of 13.5)' % (self.DozA.qty_available))
        # Check quants and available quantity for product SDozA
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.SDozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 19, 'Expecting 19 SDozen , got %.4f SDozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.SDozA.qty_available, 19, 'Wrong quantity available (%s found instead of 19)' % (self.SDozA.qty_available))
        # Check quants and available quantity for product gB.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.gB.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(round(sum(total_qty), 1), 548.3, 'Expecting 547.6 g , got %.4f g on location stock!' % (sum(total_qty)))
        self.assertEqual(round(self.gB.qty_available, 1), 548.3, 'Wrong quantity available (%s found instead of 547.6)' % (self.gB.qty_available))
        # Check quants and available quantity for product kgB.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.kgB.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 0.019, 'Expecting 0.019 kg , got %.4f kg on location stock!' % (sum(total_qty)))
        self.assertEqual(self.kgB.qty_available, 0.019, 'Wrong quantity available (%s found instead of 0.019)' % (self.kgB.qty_available))

        # ----------------------------------------------------------------------
        # Receipt back order of incoming shipment.
        # ----------------------------------------------------------------------

        bo_in_B.button_validate()
        # Check quants and available quantity for product kgB.
        quants = self.StockQuantObj.search([
            ('product_id', '=', self.DozA.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 15.5, 'Expecting 15.5 Dozen , got %.4f Dozen on location stock!' % (sum(total_qty)))
        self.assertEqual(self.DozA.qty_available, 15.5, 'Wrong quantity available (%s found instead of 15.5)' % (self.DozA.qty_available))

        # -----------------------------------------
        # Create product in kg and receive in ton.
        # -----------------------------------------

        productKG = self.ProductObj.create({'name': 'Product KG', 'uom_id': self.uom_kg.id, 'is_storable': True})
        picking_in = self.PickingObj.create({
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'state': 'draft',
            'location_dest_id': self.stock_location.id,
        })
        self.MoveObj.create({
            'product_id': productKG.id,
            'product_uom_qty': 1.0,
            'product_uom': self.uom_ton.id,
            'picking_id': picking_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        # Check incoming shipment state.
        self.assertEqual(picking_in.state, 'draft', 'Incoming shipment state should be draft.')
        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'draft', 'Wrong state of move line.')
        # Confirm incoming shipment.
        picking_in.action_confirm()
        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'assigned', 'Wrong state of move line.')
        # Check pack operation quantity.
        packKG = self.StockPackObj.search([('product_id', '=', productKG.id), ('picking_id', '=', picking_in.id)], limit=1)
        self.assertEqual(packKG.quantity_product_uom, 1000, 'Wrong product real quantity in pack operation (%s found instead of 1000)' % (packKG.quantity_product_uom))
        self.assertEqual(packKG.quantity, 1, 'Wrong product quantity in pack operation (%s found instead of 1)' % (packKG.quantity))
        self.assertEqual(packKG.product_uom_id.id, self.uom_ton.id, 'Wrong product uom in pack operation.')
        # Transfer Incoming shipment.
        picking_in.button_validate()

        # -----------------------------------------------------------------------
        # Check incoming shipment after transfer.
        # -----------------------------------------------------------------------

        # Check incoming shipment state.
        self.assertEqual(picking_in.state, 'done', 'Incoming shipment state: %s instead of %s' % (picking_in.state, 'done'))
        # Check incoming shipment move lines state.
        for move in picking_in.move_ids:
            self.assertEqual(move.state, 'done', 'Wrong state of move lines.')
        # Check total done move lines for incoming shipment.
        self.assertEqual(len(picking_in.move_ids), 1, 'Wrong number of move lines')
        # Check product DozA done quantity.
        move = self.MoveObj.search([('product_id', '=', productKG.id), ('picking_id', '=', picking_in.id)], limit=1)
        self.assertEqual(move.product_uom_qty, 1, 'Wrong product quantity in done move.')
        self.assertEqual(move.product_uom.id, self.uom_ton.id, 'Wrong unit of measure in done move.')
        self.assertEqual(productKG.qty_available, 1000, 'Wrong quantity available of product (%s found instead of 1000)' % (productKG.qty_available))
        picking_out = self.PickingObj.create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'state': 'draft',
            'location_dest_id': self.customer_location.id,
        })
        self.MoveObj.create({
            'product_id': productKG.id,
            'product_uom_qty': 25,
            'product_uom': self.uom_gm.id,
            'picking_id': picking_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        picking_out.action_confirm()
        picking_out.action_assign()
        pack_opt = self.StockPackObj.search([('product_id', '=', productKG.id), ('picking_id', '=', picking_out.id)], limit=1)
        pack_opt.write({'quantity': 5})
        res_dict_for_back_order = picking_out.button_validate()
        backorder_wizard = self.env[(res_dict_for_back_order.get('res_model'))].browse(res_dict_for_back_order.get('res_id')).with_context(res_dict_for_back_order['context'])
        backorder_wizard.process()
        quants = self.StockQuantObj.search([
            ('product_id', '=', productKG.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        # Check total quantity stock location.
        self.assertEqual(sum(total_qty), 999.995, 'Expecting 999.995 kg , got %.4f kg on location stock!' % (sum(total_qty)))

        # ---------------------------------
        # Check Back order created or not.
        # ---------------------------------
        bo_out_1 = self.PickingObj.search([('backorder_id', '=', picking_out.id)])
        self.assertEqual(len(bo_out_1), 1, 'Back order should be created.')
        # Check total move lines of back order.
        self.assertEqual(len(bo_out_1.move_ids), 1, 'Wrong number of move lines')
        moves_KG = self.MoveObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_1.id)], limit=1)
        # Check back order created with correct quantity and uom or not.
        self.assertEqual(moves_KG.product_uom_qty, 20, 'Wrong move quantity (%s found instead of 20)' % (moves_KG.product_uom_qty))
        self.assertEqual(moves_KG.product_uom.id, self.uom_gm.id, 'Wrong uom in move for product KG.')
        bo_out_1.action_assign()
        pack_opt = self.StockPackObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_1.id)], limit=1)
        pack_opt.write({'quantity': 5})
        res_dict_for_back_order = bo_out_1.button_validate()
        backorder_wizard = self.env[(res_dict_for_back_order.get('res_model'))].browse(res_dict_for_back_order.get('res_id')).with_context(res_dict_for_back_order['context'])
        backorder_wizard.process()
        quants = self.StockQuantObj.search([
            ('product_id', '=', productKG.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]

        # Check total quantity stock location.
        self.assertEqual(sum(total_qty), 999.990, 'Expecting 999.990 kg , got %.4f kg on location stock!' % (sum(total_qty)))

        # Check Back order created or not.
        # ---------------------------------
        bo_out_2 = self.PickingObj.search([('backorder_id', '=', bo_out_1.id)])
        self.assertEqual(len(bo_out_2), 1, 'Back order should be created.')
        # Check total move lines of back order.
        self.assertEqual(len(bo_out_2.move_ids), 1, 'Wrong number of move lines')
        # Check back order created with correct move quantity and uom or not.
        moves_KG = self.MoveObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_2.id)], limit=1)
        self.assertEqual(moves_KG.product_uom_qty, 15, 'Wrong move quantity (%s found instead of 15)' % (moves_KG.product_uom_qty))
        self.assertEqual(moves_KG.product_uom.id, self.uom_gm.id, 'Wrong uom in move for product KG.')
        bo_out_2.action_assign()
        pack_opt = self.StockPackObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_2.id)], limit=1)
        pack_opt.write({'quantity': 5})
        res_dict_for_back_order = bo_out_2.button_validate()
        backorder_wizard = self.env[(res_dict_for_back_order.get('res_model'))].browse(res_dict_for_back_order.get('res_id')).with_context(res_dict_for_back_order['context'])
        backorder_wizard.process()
        # Check total quantity stock location of product KG.
        quants = self.StockQuantObj.search([
            ('product_id', '=', productKG.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 999.985, 'Expecting 999.985 kg , got %.4f kg on location stock!' % (sum(total_qty)))

        # Check Back order created or not.
        # ---------------------------------
        bo_out_3 = self.PickingObj.search([('backorder_id', '=', bo_out_2.id)])
        self.assertEqual(len(bo_out_3), 1, 'Back order should be created.')
        # Check total move lines of back order.
        self.assertEqual(len(bo_out_3.move_ids), 1, 'Wrong number of move lines')
        # Check back order created with correct quantity and uom or not.
        moves_KG = self.MoveObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_3.id)], limit=1)
        self.assertEqual(moves_KG.product_uom_qty, 10, 'Wrong move quantity (%s found instead of 10)' % (moves_KG.product_uom_qty))
        self.assertEqual(moves_KG.product_uom.id, self.uom_gm.id, 'Wrong uom in move for product KG.')
        bo_out_3.action_assign()
        pack_opt = self.StockPackObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_3.id)], limit=1)
        pack_opt.write({'quantity': 5})
        res_dict_for_back_order = bo_out_3.button_validate()
        backorder_wizard = self.env[(res_dict_for_back_order.get('res_model'))].browse(res_dict_for_back_order.get('res_id')).with_context(res_dict_for_back_order['context'])
        backorder_wizard.process()
        quants = self.StockQuantObj.search([
            ('product_id', '=', productKG.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertEqual(sum(total_qty), 999.980, 'Expecting 999.980 kg , got %.4f kg on location stock!' % (sum(total_qty)))

        # Check Back order created or not.
        # ---------------------------------
        bo_out_4 = self.PickingObj.search([('backorder_id', '=', bo_out_3.id)])

        self.assertEqual(len(bo_out_4), 1, 'Back order should be created.')
        # Check total move lines of back order.
        self.assertEqual(len(bo_out_4.move_ids), 1, 'Wrong number of move lines')
        # Check back order created with correct quantity and uom or not.
        moves_KG = self.MoveObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_4.id)], limit=1)
        self.assertEqual(moves_KG.product_uom_qty, 5, 'Wrong move quantity (%s found instead of 5)' % (moves_KG.product_uom_qty))
        self.assertEqual(moves_KG.product_uom.id, self.uom_gm.id, 'Wrong uom in move for product KG.')
        bo_out_4.action_assign()
        pack_opt = self.StockPackObj.search([('product_id', '=', productKG.id), ('picking_id', '=', bo_out_4.id)], limit=1)
        pack_opt.write({'quantity': 5})
        bo_out_4.button_validate()
        quants = self.StockQuantObj.search([
            ('product_id', '=', productKG.id), ('location_id', '=', self.stock_location.id)
        ])
        total_qty = [quant.quantity for quant in quants]
        self.assertAlmostEqual(sum(total_qty), 999.975, msg='Expecting 999.975 kg , got %.4f kg on location stock!' % (sum(total_qty)))