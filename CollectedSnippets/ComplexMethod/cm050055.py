def _import_invoice_ubl_cii(self, invoice, file_data, new=False):
        invoice.ensure_one()
        if invoice.invoice_line_ids:
            return invoice._reason_cannot_decode_has_invoice_lines()

        tree = file_data['xml_tree']

        # Not able to decode the move_type from the xml.
        move_type, qty_factor = self._get_import_document_amount_sign(tree)
        if not move_type:
            return

        # Check for inconsistent move_type.
        journal = invoice.journal_id
        if journal.type == 'sale':
            move_type = 'out_' + move_type
        elif journal.type == 'purchase':
            move_type = 'in_' + move_type
        else:
            return
        if not new and invoice.move_type != move_type:
            # with an email alias to create account_move, first the move is created (using alias_defaults, which
            # contains move_type = 'out_invoice') then the attachment is decoded, if it represents a credit note,
            # the move type needs to be changed to 'out_refund'
            types = {move_type, invoice.move_type}
            if types == {'out_invoice', 'out_refund'} or types == {'in_invoice', 'in_refund'}:
                invoice.move_type = move_type
            else:
                return

        # Update the invoice.
        invoice.move_type = move_type
        with invoice._get_edi_creation() as invoice:
            fill_invoice_logs = self._import_fill_invoice(invoice, tree, qty_factor)

        # For UBL, we should override the computed tax amount if it is less than 0.05 different of the one in the xml.
        # In order to support use case where the tax total is adapted for rounding purpose.
        # This has to be done after the first import in order to let Odoo compute the taxes before overriding if needed.
        with invoice._get_edi_creation() as invoice:
            self._correct_invoice_tax_amount(tree, invoice)

        # Set XML as ubl_cii_xml_file (XML used to import)
        if file_data['attachment'] and invoice.is_purchase_document(include_receipts=True):
            file_data['attachment'].write({
                'res_field': 'ubl_cii_xml_file',
                'res_model': invoice._name,
                'res_id': invoice.id,
            })

        source_attachment = file_data['attachment'] or self.env['ir.attachment']
        attachments = source_attachment + self._import_attachments(invoice, tree)

        self._log_import_invoice_ubl_cii(invoice, invoice_logs=fill_invoice_logs, attachments=attachments)