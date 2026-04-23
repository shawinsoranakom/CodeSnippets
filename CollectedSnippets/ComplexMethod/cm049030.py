def test_refund_modify(self):
        """ Test invoice with a refund in 'modify' mode, and check customer invoices credit note is created from respective invoice """
        # Decrease quantity of an invoice lines
        with Form(self.invoice) as invoice_form:
            with invoice_form.invoice_line_ids.edit(0) as line_form:
                line_form.quantity = 3
            with invoice_form.invoice_line_ids.edit(1) as line_form:
                line_form.quantity = 2

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
                    self.assertEqual(line.qty_to_invoice, 2.0, "The ordered sale line are totally invoiced (qty to invoice is zero)")
                    self.assertEqual(line.qty_invoiced, 3.0, "The ordered (prod) sale line are totally invoiced (qty invoiced come from the invoice lines)")
                else:
                    self.assertEqual(line.qty_to_invoice, 1.0, "The ordered sale line are totally invoiced (qty to invoice is zero)")
                    self.assertEqual(line.qty_invoiced, 2.0, "The ordered (serv) sale line are totally invoiced (qty invoiced = the invoice lines)")
                self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * line.qty_to_invoice, "Amount to invoice is now set as qty to invoice * unit price since no price change on invoice, for ordered products")
                self.assertEqual(line.untaxed_amount_invoiced, line.price_unit * line.qty_invoiced, "Amount invoiced is now set as qty invoiced * unit price since no price change on invoice, for ordered products")
                self.assertEqual(len(line.invoice_lines), 1, "The lines 'ordered' qty are invoiced, so it should be linked to 1 invoice lines")

        # Make a credit note
        credit_note_wizard = self.env['account.move.reversal'].with_context({'active_ids': [self.invoice.id], 'active_id': self.invoice.id, 'active_model': 'account.move'}).create({
            'reason': 'reason test modify',
            'journal_id': self.invoice.journal_id.id,
        })
        invoice_refund = self.env['account.move'].browse(credit_note_wizard.modify_moves()['res_id'])

        # Check invoice's type and number
        self.assertEqual(invoice_refund.move_type, 'out_invoice', 'The last created invoiced should be a customer invoice')
        self.assertEqual(invoice_refund.state, 'draft', 'Last Customer invoices should be in draft')
        self.assertEqual(self.sale_order.invoice_count, 3, "The SO should have 3 related invoices: the original, the refund, and the new one")
        self.assertEqual(len(self.sale_order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_refund')), 1, "The SO should be linked to only one refund")
        self.assertEqual(len(self.sale_order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice')), 2, "The SO should be linked to two customer invoices")

        # At this time, the invoice 1 and its refund are confirmed, so the amounts invoiced are zero. The third invoice
        # (2nd customer inv) is in draft state.
        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be same as ordered quantity")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as no any invoice created for SO")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
                self.assertFalse(line.invoice_lines, "The line based on delivered are not invoiced, so they should not be linked to invoice line")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(line.qty_to_invoice, 2.0, "The qty to invoice does not change when confirming the new invoice (2)")
                    self.assertEqual(line.qty_invoiced, 3.0, "The ordered (prod) sale line does not change on invoice 2 confirmation")
                    self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * 5, "Amount to invoice is now set as qty to invoice * unit price since no price change on invoice, for ordered products")
                    self.assertEqual(line.untaxed_amount_invoiced, 0.0, "Amount invoiced is zero as the invoice 1 and its refund are reconcilied")
                    self.assertEqual(len(line.invoice_lines), 3, "The line 'ordered consumable' is invoiced, so it should be linked to 3 invoice lines (invoice and refund)")
                else:
                    self.assertEqual(line.qty_to_invoice, 1.0, "The qty to invoice does not change when confirming the new invoice (2)")
                    self.assertEqual(line.qty_invoiced, 2.0, "The ordered (serv) sale line does not change on invoice 2 confirmation")
                    self.assertEqual(line.untaxed_amount_to_invoice, line.price_unit * 3, "Amount to invoice is now set as unit price * ordered qty - refund qty) even if the ")
                    self.assertEqual(line.untaxed_amount_invoiced, 0.0, "Amount invoiced is zero as the invoice 1 and its refund are reconcilied")
                    self.assertEqual(len(line.invoice_lines), 3, "The line 'ordered service' is invoiced, so it should be linked to 3 invoice lines (invoice and refund)")

        # Change unit of ordered product on refund lines
        move_form = Form(invoice_refund)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.price_unit = 100
        with move_form.invoice_line_ids.edit(1) as line_form:
            line_form.price_unit = 50
        invoice_refund = move_form.save()

        # Validate the refund
        invoice_refund.action_post()

        for line in self.sale_order.order_line:
            if line.product_id.invoice_policy == 'delivery':
                self.assertEqual(line.qty_to_invoice, 0.0, "Quantity to invoice should be same as ordered quantity")
                self.assertEqual(line.qty_invoiced, 0.0, "Invoiced quantity should be zero as no any invoice created for SO")
                self.assertEqual(line.untaxed_amount_to_invoice, 0.0, "The amount to invoice should be zero, as the line based on delivered quantity")
                self.assertEqual(line.untaxed_amount_invoiced, 0.0, "The invoiced amount should be zero, as the line based on delivered quantity")
                self.assertFalse(line.invoice_lines, "The line based on delivered are not invoiced, so they should not be linked to invoice line, even after validation")
            else:
                if line == self.sol_prod_order:
                    self.assertEqual(line.qty_to_invoice, 2.0, "The qty to invoice does not change when confirming the new invoice (3)")
                    self.assertEqual(line.qty_invoiced, 3.0, "The ordered sale line are totally invoiced (qty invoiced = ordered qty)")
                    self.assertEqual(line.untaxed_amount_to_invoice, 1100.0, "")
                    self.assertEqual(line.untaxed_amount_invoiced, 300.0, "")
                    self.assertEqual(len(line.invoice_lines), 3, "The line 'ordered consumable' is invoiced, so it should be linked to 2 invoice lines (invoice and refund), even after validation")
                else:
                    self.assertEqual(line.qty_to_invoice, 1.0, "The qty to invoice does not change when confirming the new invoice (3)")
                    self.assertEqual(line.qty_invoiced, 2.0, "The ordered sale line are totally invoiced (qty invoiced = ordered qty)")
                    self.assertEqual(line.untaxed_amount_to_invoice, 170.0, "")
                    self.assertEqual(line.untaxed_amount_invoiced, 100.0, "")
                    self.assertEqual(len(line.invoice_lines), 3, "The line 'ordered service' is invoiced, so it should be linked to 2 invoice lines (invoice and refund), even after validation")