def test_invoice(self):
        """ Test create and invoice from the SO, and check qty invoice/to invoice, and the related amounts """
        # lines are in draft
        for line in self.sale_order.order_line:
            self.assertTrue(float_is_zero(line.untaxed_amount_to_invoice, precision_digits=2), "The amount to invoice should be zero, as the line is in draf state")
            self.assertTrue(float_is_zero(line.untaxed_amount_invoiced, precision_digits=2), "The invoiced amount should be zero, as the line is in draft state")

        # Confirm the SO
        self.sale_order.action_confirm()

        # Check ordered quantity, quantity to invoice and invoiced quantity of SO lines
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, 'Quantity to invoice should be same as ordered quantity')
                self.assertEqual(line.qty_invoiced, 0.0, 'Invoiced quantity should be zero as no any invoice created for SO')
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
            else:
                self.assertEqual(line.qty_to_invoice, line.product_uom_qty, 'Quantity to invoice should be same as ordered quantity')
                self.assertEqual(line.qty_invoiced, 0.0, 'Invoiced quantity should be zero as no any invoice created for SO')
                self.assertEqual(line.untaxed_amount_to_invoice, line.product_uom_qty * line.price_unit, "The amount to invoice should the total of the line, as the line is confirmed")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line is confirmed")

        # Let's do an invoice with invoiceable lines
        payment = self.env['sale.advance.payment.inv'].with_context(self.context).create({
            'advance_payment_method': 'delivered'
        })
        payment.create_invoices()

        invoice = self.sale_order.invoice_ids[0]

        # Update quantity of an invoice lines
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.quantity = 3.0
        with move_form.invoice_line_ids.edit(1) as line_form:
            line_form.quantity = 2.0
        invoice = move_form.save()

        # amount to invoice / invoiced should not have changed (amounts take only confirmed invoice into account)
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be zero")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as delivered lines are not delivered yet")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity (no confirmed invoice)")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as no invoice are validated for now")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(self.sol_prod_order.qty_to_invoice, 2.0, "Changing the quantity on draft invoice update the qty to invoice on SO lines")
                    self.assertEqual(self.sol_prod_order.qty_invoiced, 3.0, "Changing the quantity on draft invoice update the invoiced qty on SO lines")
                else:
                    self.assertEqual(self.sol_serv_order.qty_to_invoice, 1.0, "Changing the quantity on draft invoice update the qty to invoice on SO lines")
                    self.assertEqual(self.sol_serv_order.qty_invoiced, 2.0, "Changing the quantity on draft invoice update the invoiced qty on SO lines")
                self.assertEqual(line.untaxed_amount_to_invoice, line.product_uom_qty * line.price_unit, "The amount to invoice should the total of the line, as the line is confirmed (no confirmed invoice)")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as no invoice are validated for now")

        invoice.button_cancel()
        # amount to invoice / invoiced should should be reset
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, 'Quantity to invoice should be same as ordered quantity')
                self.assertEqual(line.qty_invoiced, 0.0, 'Invoiced quantity should be zero as no any invoice created for SO')
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
            else:
                self.assertEqual(line.qty_to_invoice, line.product_uom_qty, 'Quantity to invoice should be same as ordered quantity')
                self.assertEqual(line.qty_invoiced, 0.0, 'Invoiced quantity should be zero as no any invoice created for SO')
                self.assertEqual(line.untaxed_amount_to_invoice, line.product_uom_qty * line.price_unit, "The amount to invoice should the total of the line, as the line is confirmed")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line is confirmed")

        invoice.button_draft()
        invoice.action_post()

        # Check quantity to invoice on SO lines
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be same as ordered quantity")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as no any invoice created for SO")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(line.qty_to_invoice, 2.0, "The ordered sale line are totally invoiced (qty to invoice is zero)")
                    self.assertEqual(line.qty_invoiced, 3.0, "The ordered (prod) sale line are totally invoiced (qty invoiced come from the invoice lines)")
                else:
                    self.assertEqual(line.qty_to_invoice, 1.0, "The ordered sale line are totally invoiced (qty to invoice is zero)")
                    self.assertEqual(line.qty_invoiced, 2.0, "The ordered (serv) sale line are totally invoiced (qty invoiced = the invoice lines)")
                self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * line.qty_to_invoice, "Amount to invoice is now set as qty to invoice * unit price since no price change on invoice, for ordered products")
                self.assertEqual(line.untaxed_amount_invoiced, line.price_unit * line.qty_invoiced, "Amount invoiced is now set as qty invoiced * unit price since no price change on invoice, for ordered products")