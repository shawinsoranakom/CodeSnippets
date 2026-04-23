def test_00_sale_stock_invoice(self):
        """
        Test SO's changes when playing around with stock moves, quants, pack operations, pickings
        and whatever other model there is in stock with "invoice on delivery" products
        """
        self.so = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'partner_invoice_id': self.partner_a.id,
            'partner_shipping_id': self.partner_a.id,
            'order_line': [
                (0, 0, {
                    'name': p.name,
                    'product_id': p.id,
                    'product_uom_qty': 2,
                    'price_unit': p.list_price,
                }) for p in (
                    self.company_data['product_order_no'],
                    self.company_data['product_service_delivery'],
                    self.company_data['product_service_order'],
                    self.company_data['product_delivery_no'],
                )],
            'picking_policy': 'direct',
        })

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(self.so.picking_ids, 'Sale Stock: no picking created for "invoice on delivery" storable products')
        # invoice on order
        self.so._create_invoices()

        # deliver partially, check the so's invoice_status and delivered quantities
        self.assertEqual(self.so.invoice_status, 'no', 'Sale Stock: so invoice_status should be "nothing to invoice" after invoicing')
        pick = self.so.picking_ids
        pick.move_ids.write({'quantity': 1, 'picked': True})
        Form.from_action(self.env, pick.button_validate()).save().process()
        self.assertEqual(self.so.invoice_status, 'to invoice', 'Sale Stock: so invoice_status should be "to invoice" after partial delivery')
        del_qties = [sol.qty_delivered for sol in self.so.order_line]
        del_qties_truth = [1.0 if sol.product_id.type == 'consu' else 0.0 for sol in self.so.order_line]
        self.assertEqual(del_qties, del_qties_truth, 'Sale Stock: delivered quantities are wrong after partial delivery')
        # invoice on delivery: only storable products
        inv_1 = self.so._create_invoices()
        self.assertTrue(all([il.product_id.invoice_policy == 'delivery' for il in inv_1.invoice_line_ids]),
                        'Sale Stock: invoice should only contain "invoice on delivery" products')

        # complete the delivery and check invoice_status again
        self.assertEqual(self.so.invoice_status, 'no',
                         'Sale Stock: so invoice_status should be "nothing to invoice" after partial delivery and invoicing')
        self.assertEqual(len(self.so.picking_ids), 2, 'Sale Stock: number of pickings should be 2')
        pick_2 = self.so.picking_ids.filtered('backorder_id')
        pick_2.move_ids.write({'quantity': 1, 'picked': True})
        self.assertTrue(pick_2.button_validate(), 'Sale Stock: second picking should be final without need for a backorder')
        self.assertEqual(self.so.invoice_status, 'to invoice', 'Sale Stock: so invoice_status should be "to invoice" after complete delivery')
        del_qties = [sol.qty_delivered for sol in self.so.order_line]
        del_qties_truth = [2.0 if sol.product_id.type == 'consu' else 0.0 for sol in self.so.order_line]
        self.assertEqual(del_qties, del_qties_truth, 'Sale Stock: delivered quantities are wrong after complete delivery')
        # Without timesheet, we manually set the delivered qty for the product serv_del
        self.so.order_line.sorted()[1]['qty_delivered'] = 2.0

        # There is a bug with `new` and `_origin`
        # If you create a first new from a record, then change a value on the origin record, than create another new,
        # this other new wont have the updated value of the origin record, but the one from the previous new
        # Here the problem lies in the use of `new` in `move = self_ctx.new(new_vals)`,
        # and the fact this method is called multiple times in the same transaction test case.
        # Here, we update `qty_delivered` on the origin record, but the `new` records which are in cache with this order line
        # as origin are not updated, nor the fields that depends on it.
        self.env.flush_all()
        self.env.invalidate_all()

        inv_id = self.so._create_invoices()
        self.assertEqual(self.so.invoice_status, 'invoiced',
                         'Sale Stock: so invoice_status should be "fully invoiced" after complete delivery and invoicing')