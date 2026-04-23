def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_after_invoice_pdf_render(invoices_data)
        for invoice, invoice_data in invoices_data.items():
            # Handle the json file, and create it if it does not yet exist. This can be done without sending to the EDI.
            json_file_data = [file for file in invoice_data.get('sinvoice_attachments', []) if file['mimetype'] == 'application/json']

            if not invoice.l10n_vn_edi_sinvoice_file and json_file_data:
                self.env['ir.attachment'].with_user(SUPERUSER_ID).create(json_file_data)
                invoice.invalidate_recordset(fnames=[
                    'l10n_vn_edi_sinvoice_file_id',
                    'l10n_vn_edi_sinvoice_file',
                ])

            if invoice.l10n_vn_edi_invoice_state != 'sent':
                continue

            if not self.env.context.get('skip_fetch_sinvoice_files'):
                error = invoice._l10n_vn_edi_fetch_invoice_files()
                if error:
                    invoice_data['error'] = error

            if self._can_commit():
                self.env.cr.commit()