def test_00_purchase_order_flow(self):
        # Ensure product_id_2 doesn't have res_partner_1 as supplier
        if self.partner_a in self.product_id_2.seller_ids.partner_id:
            id_to_remove = self.product_id_2.seller_ids.filtered(lambda r: r.partner_id == self.partner_a).ids[0] if self.product_id_2.seller_ids.filtered(lambda r: r.partner_id == self.partner_a) else False
            if id_to_remove:
                self.product_id_2.write({
                    'seller_ids': [(2, id_to_remove, False)],
                })
        self.assertFalse(self.product_id_2.seller_ids.filtered(lambda r: r.partner_id == self.partner_a), 'Purchase: the partner should not be in the list of the product suppliers')

        self.po = self.env['purchase.order'].create(self.po_vals)
        self.assertTrue(self.po, 'Purchase: no purchase order created')
        self.assertEqual(self.po.invoice_status, 'no', 'Purchase: PO invoice_status should be "Not purchased"')
        self.assertEqual(self.po.order_line.mapped('qty_received'), [0.0, 0.0], 'Purchase: no product should be received"')
        self.assertEqual(self.po.order_line.mapped('qty_invoiced'), [0.0, 0.0], 'Purchase: no product should be invoiced"')

        self.po.button_confirm()
        self.assertEqual(self.po.state, 'purchase', 'Purchase: PO state should be "Purchase"')
        self.assertEqual(self.po.invoice_status, 'to invoice', 'Purchase: PO invoice_status should be "Waiting Invoices"')

        self.assertTrue(self.product_id_2.seller_ids.filtered(lambda r: r.partner_id == self.partner_a), 'Purchase: the partner should be in the list of the product suppliers')

        seller = self.product_id_2._select_seller(partner_id=self.partner_a, quantity=2.0, date=self.po.date_planned, uom_id=self.product_id_2.uom_id)
        price_unit = seller.price if seller else 0.0
        if price_unit and seller and self.po.currency_id and seller.currency_id != self.po.currency_id:
            price_unit = seller.currency_id._convert(price_unit, self.po.currency_id, self.po.company_id, self.po.date_order)
        self.assertEqual(price_unit, 250.0, 'Purchase: the price of the product for the supplier should be 250.0.')

        self.assertEqual(self.po.incoming_picking_count, 1, 'Purchase: one picking should be created"')
        self.picking = self.po.picking_ids[0]
        self.picking.move_line_ids.write({'quantity': 5.0})
        self.picking.move_ids.picked = True
        self.picking.button_validate()
        self.assertEqual(self.po.order_line.mapped('qty_received'), [5.0, 5.0], 'Purchase: all products should be received"')

        move_form = Form(self.env['account.move'].with_context(default_move_type='in_invoice'))
        move_form.partner_id = self.partner_a
        move_form.purchase_vendor_bill_id = self.env['purchase.bill.union'].browse(-self.po.id)
        self.invoice = move_form.save()

        self.assertEqual(self.po.order_line.mapped('qty_invoiced'), [5.0, 5.0], 'Purchase: all products should be invoiced"')