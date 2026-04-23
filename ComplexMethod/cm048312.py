def _l10n_vn_edi_fetch_invoice_files(self):
        """
        Fetches the SInvoice XML and PDF data from the SInvoice server if self is a sent invoice.
        The files are saved in the l10n_vn_edi_sinvoice_pdf_file_id and l10n_vn_edi_sinvoice_xml_file_id.
        """

        if self.l10n_vn_edi_invoice_state != 'sent':
            raise UserError(_("Please send the invoice to SInvoice before fetching the tax invoice files."))

        xml_data, xml_error_message = self._l10n_vn_edi_fetch_invoice_xml_file_data()
        pdf_data, pdf_error_message = self._l10n_vn_edi_fetch_invoice_pdf_file_data()

        # Not using _link_invoice_documents for these because it depends on _need_invoice_document and I can't get it to work
        # well while allowing users to download the files before sending.
        attachments_data = []
        for file, error in [(xml_data, xml_error_message), (pdf_data, pdf_error_message)]:
            if error:
                continue

            attachments_data.append({
                'name': file['name'],
                'raw': file['raw'],
                'mimetype': file['mimetype'],
                'res_model': self._name,
                'res_id': self.id,
                'res_field': file['res_field'],  # Binary field
            })

        if attachments_data:
            attachments = self.env['ir.attachment'].with_user(SUPERUSER_ID).create(attachments_data)
            self.invalidate_recordset(fnames=[
                'l10n_vn_edi_sinvoice_xml_file_id',
                'l10n_vn_edi_sinvoice_xml_file',
                'l10n_vn_edi_sinvoice_pdf_file_id',
                'l10n_vn_edi_sinvoice_pdf_file',
            ])

            # Log the new attachment in the chatter for reference. Make sure to add the JSON file.
            self.with_context(no_new_invoice=True).message_post(
                body=_('Invoice sent to SInvoice'),
                attachment_ids=attachments.ids + self.l10n_vn_edi_sinvoice_file_id.ids,
            )

        if xml_error_message or pdf_error_message:
            return {
                'error_title': _('Error when receiving SInvoice files.'),
                'errors': [error_message for error_message in [xml_error_message, pdf_error_message] if error_message],
            }