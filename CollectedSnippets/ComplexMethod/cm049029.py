def test_refund_create(self):
        # Validate invoice
        self.invoice.action_post()

        # Check quantity to invoice on SO lines
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be same as ordered quantity")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as no any invoice created for SO")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
                self.assertFalse(line.invoice_lines, "The line based on delivered qty are not invoiced, so they should not be linked to invoice line")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(line.qty_to_invoice, 0.0, "The ordered sale line are totally invoiced (qty to invoice is zero)")
                    self.assertEqual(line.qty_invoiced, 5.0, "The ordered (prod) sale line are totally invoiced (qty invoiced come from the invoice lines)")
                else:
                    self.assertEqual(line.qty_to_invoice, 0.0, "The ordered sale line are totally invoiced (qty to invoice is zero)")
                    self.assertEqual(line.qty_invoiced, 3.0, "The ordered (serv) sale line are totally invoiced (qty invoiced = the invoice lines)")
                self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * line.qty_to_invoice, "Amount to invoice is now set as qty to invoice * unit price since no price change on invoice, for ordered products")
                self.assertEqual(line.untaxed_amount_invoiced, line.price_unit * line.qty_invoiced, "Amount invoiced is now set as qty invoiced * unit price since no price change on invoice, for ordered products")
                self.assertEqual(len(line.invoice_lines), 1, "The lines 'ordered' qty are invoiced, so it should be linked to 1 invoice lines")

        # Make a credit note
        credit_note_wizard = self.env['account.move.reversal'].with_context({'active_ids': [self.invoice.id], 'active_id': self.invoice.id, 'active_model': 'account.move'}).create({
            'reason': 'reason test create',
            'journal_id': self.invoice.journal_id.id,
        })
        credit_note_wizard.refund_moves()
        invoice_refund = self.sale_order.invoice_ids.sorted(key=lambda inv: inv.id, reverse=False)[-1]  # the first invoice, its refund, and the new invoice

        # Check invoice's type and number
        self.assertEqual(invoice_refund.move_type, 'out_refund', 'The last created invoiced should be a refund')
        self.assertEqual(invoice_refund.state, 'draft', 'Last Customer invoices should be in draft')
        self.assertEqual(self.sale_order.invoice_count, 2, "The SO should have 2 related invoices: the original, the new refund")
        self.assertEqual(len(self.sale_order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_refund')), 1, "The SO should be linked to only one refund")
        self.assertEqual(len(self.sale_order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice')), 1, "The SO should be linked to only one customer invoices")

        # At this time, the invoice 1 is opend (validated) and its refund is in draft, so the amounts invoiced are not zero for
        # invoiced sale line. The amounts only take validated invoice/refund into account.
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be same as ordered quantity")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as no any invoice created for SO line based on delivered qty")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
                self.assertFalse(line.invoice_lines, "The line based on delivered are not invoiced, so they should not be linked to invoice line")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(line.qty_to_invoice, 5.0, "As the refund is created, the invoiced quantity cancel each other (consu ordered)")
                    self.assertEqual(line.qty_invoiced, 0.0, "The qty to invoice should have decreased as the refund is created for ordered consu SO line")
                    self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "Amount to invoice is zero as the refund is not validated")
                    self.assertEqual(line.untaxed_amount_invoiced, line.price_unit * 5, "Amount invoiced is now set as unit price * ordered qty - refund qty) even if the ")
                    self.assertEqual(len(line.invoice_lines), 2, "The line 'ordered consumable' is invoiced, so it should be linked to 2 invoice lines (invoice and refund)")
                else:
                    self.assertEqual(line.qty_to_invoice, 3.0, "As the refund is created, the invoiced quantity cancel each other (consu ordered)")
                    self.assertEqual(line.qty_invoiced, 0.0, "The qty to invoice should have decreased as the refund is created for ordered service SO line")
                    self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "Amount to invoice is zero as the refund is not validated")
                    self.assertEqual(line.untaxed_amount_invoiced, line.price_unit * 3, "Amount invoiced is now set as unit price * ordered qty - refund qty) even if the ")
                    self.assertEqual(len(line.invoice_lines), 2, "The line 'ordered service' is invoiced, so it should be linked to 2 invoice lines (invoice and refund)")

        # Validate the refund
        invoice_refund.action_post()

        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be same as ordered quantity")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as no any invoice created for SO")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
                self.assertFalse(line.invoice_lines, "The line based on delivered are not invoiced, so they should not be linked to invoice line")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(line.qty_to_invoice, 5.0, "As the refund still exists, the quantity to invoice is the ordered quantity")
                    self.assertEqual(line.qty_invoiced, 0.0, "The qty to invoice should be zero as, with the refund, the quantities cancel each other")
                    self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * 5, "Amount to invoice is now set as qty to invoice * unit price since no price change on invoice, as refund is validated")
                    self.assertEqual(line.untaxed_amount_invoiced, 0.0, "Amount invoiced decreased as the refund is now confirmed")
                    self.assertEqual(len(line.invoice_lines), 2, "The line 'ordered consumable' is invoiced, so it should be linked to 2 invoice lines (invoice and refund)")
                else:
                    self.assertEqual(line.qty_to_invoice, 3.0, "As the refund still exists, the quantity to invoice is the ordered quantity")
                    self.assertEqual(line.qty_invoiced, 0.0, "The qty to invoice should be zero as, with the refund, the quantities cancel each other")
                    self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * 3, "Amount to invoice is now set as qty to invoice * unit price since no price change on invoice, as refund is validated")
                    self.assertEqual(line.untaxed_amount_invoiced, 0.0, "Amount invoiced decreased as the refund is now confirmed")
                    self.assertEqual(len(line.invoice_lines), 2, "The line 'ordered service' is invoiced, so it should be linked to 2 invoice lines (invoice and refund)")