def action_create_invoice(self, attachment_ids=False):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type in ('line_section', 'line_subsection'):
                    pending_section = line
                    continue
                if pending_section:
                    line_vals = pending_section._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
                    pending_section = None
                line_vals = line._prepare_account_move_line()
                line_vals.update({'sequence': sequence})
                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                sequence += 1
            invoice_vals_list.append(invoice_vals)

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for _grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
            ref_invoice_vals.update({
                'invoice_origin': ', '.join(origins),
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        invoices = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            invoices |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        invoices.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_move_type()

        # 5) Link the attachments to the invoice
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            return self.action_view_invoice(invoices)

        if len(invoices) != 1:
            raise ValidationError(_("You can only upload a bill for a single vendor at a time."))
        invoices.with_context(skip_is_manually_modified=True)._extend_with_attachments(
            invoices._to_files_data(attachments),
            new=True,
        )

        invoices.message_post(attachment_ids=attachments.ids)

        attachments.write({'res_model': 'account.move', 'res_id': invoices.id})
        return self.action_view_invoice(invoices)