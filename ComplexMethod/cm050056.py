def _import_attachments(self, invoice, tree):
        # Import the embedded documents in the xml if some are found
        attachments = self.env['ir.attachment']
        if invoice.message_main_attachment_id.mimetype == 'application/pdf':
            # Invoice look like it was already imported, don't import attachments again
            return attachments
        additional_docs = tree.findall('./{*}AdditionalDocumentReference')
        for document in additional_docs:
            attachment_name = document.find('{*}ID')
            attachment_data = document.find('{*}Attachment/{*}EmbeddedDocumentBinaryObject')
            if attachment_name is not None and attachment_data is not None:
                mimetype = attachment_data.attrib.get('mimeCode')
                if not (extension := SUPPORTED_FILE_TYPES.get(mimetype)):
                    continue
                text = attachment_data.text
                # Normalize the name of the file : some e-fff emitters put the full path of the file
                # (Windows or Linux style) and/or the name of the xml instead of the pdf.
                # Get only the filename with the right extension.
                name = (attachment_name.text or 'invoice').split('\\')[-1].split('/')[-1].split('.')[0] + extension
                attachment = self.env['ir.attachment'].create({
                    'name': name,
                    'res_id': invoice.id,
                    'res_model': 'account.move',
                    'datas': text + '=' * (len(text) % 3),  # Fix incorrect padding
                    'type': 'binary',
                    'mimetype': mimetype,
                })
                # Upon receiving an email (containing an xml) with a configured alias to create invoice, the xml is
                # set as the main_attachment. To be rendered in the form view, the pdf should be the main_attachment.
                if invoice.message_main_attachment_id and \
                        invoice.message_main_attachment_id.name.endswith('.xml') and \
                        'pdf' not in invoice.message_main_attachment_id.mimetype and \
                        mimetype == 'application/pdf':
                    invoice._message_set_main_attachment_id(attachment, force=True, filter_xml=False)
                attachments |= attachment

        return attachments