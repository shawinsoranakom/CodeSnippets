def _upload_and_import_attachments(self, origin, attachments_vals):
        """ Simulate the upload of one or more attachments and their processing by the import framework.
            Keeps track of the created attachments, messages and invoices, and returns them.

            :param origin: The source from which the attachments should be introduced into Odoo.
                           Possible values:
                                - 'chatter_message': Simulates a message posted on the chatter of an existing vendor bill.
                                - 'chatter_upload': Simulates attachments uploaded on the chatter of an existing vendor bill.
                                - 'chatter_email': Simulates an incoming e-mail on the chatter of an existing vendor bill.
                                - 'mail_alias': Simulates an incoming e-mail on a purchase journal mail alias.
                                - 'journal': Simulates attachments uploaded on a purchase journal in the dashboard.

            :param attachments_vals: A list of values representing attachments to upload into Odoo.

            :return: a dict {
                'ir.attachment': created_attachments,
                'mail.message': created_messages,
                'account.move': created_invoices,
            }
        """

        with (
            RecordCapturer(self.env['ir.attachment'].sudo()) as attachment_capturer,
            RecordCapturer(self.env['mail.message'].sudo()) as message_capturer,
            RecordCapturer(self.env['account.move']) as move_capturer,
        ):
            journal = self.company_data['default_journal_purchase']
            init_vals = {'move_type': 'in_invoice', 'journal_id': journal.id}

            if origin not in {'chatter_email', 'mail_alias'}:
                attachments = self.env['ir.attachment'].create(attachments_vals)

            if origin in {'chatter_upload', 'chatter_message', 'chatter_email'}:
                move = self.env['account.move'].create(init_vals)

            match origin:
                case 'chatter_message':
                    move.message_post(message_type='comment', attachment_ids=attachments.ids)
                case 'chatter_upload':
                    attachments.write({'res_model': 'account.move', 'res_id': move.id})
                    attachments._post_add_create()
                case 'chatter_email':
                    email_raw = self._get_raw_mail_message_str(attachments_vals, email_to='someone@example.com')
                    self.env['mail.thread'].message_process('account.move', email_raw, custom_values=init_vals, thread_id=move.id)
                case 'mail_alias':
                    email_raw = self._get_raw_mail_message_str(attachments_vals, email_to=journal.alias_id.display_name)
                    self.env['mail.thread'].message_process('account.move', email_raw, custom_values=init_vals)
                case 'journal':
                    journal.create_document_from_attachment(attachments.ids)
                case _:
                    raise ValueError(f"Unknown origin: {origin}")

        attachments_created = attachment_capturer.records
        moves = move_capturer.records
        # if account_edi_ubl_cii is installed and used as decoder, an attachment is linked to the imported bill with res_field = ubl_cii_xml_file
        # Therefore it is not detected in the attachment_capturer (because res_field is not specified in domain used to search, see `_search` method override in ir.attachment)
        # So we need to catch it as some tests check that it has been created
        if 'ubl_cii_xml_id' in moves._fields:
            attachments_created |= moves.ubl_cii_xml_id
        return attachments_created, message_capturer.records, moves