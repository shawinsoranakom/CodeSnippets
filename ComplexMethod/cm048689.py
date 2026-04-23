def _message_post_after_hook(self, new_message, message_values):
        """ This method processes the attachments of a new mail.message. It handles the 3 following situations:
            (1) receiving an e-mail from a mail alias. In that case, we potentially want to split the attachments into several invoices.
            (2) receiving an e-mail / posting a message on an existing invoice via the webclient:
                (2)(a): If the poster is an internal user, we enhance the invoice with the attachments.
                (2)(b): Otherwise, we don't do any further processing.
            (3) posting a message on an invoice in application code. In that case, don't do anything.

            Furthermore, in cases (1) and (2), we decide for each attachment whether to add it as an attachment on the invoice,
            based on its mimetype.
        """
        # EXTENDS mail mail.thread
        attachments = new_message.attachment_ids

        if not attachments or new_message.message_type not in {'email', 'comment'} or self.env.context.get('disable_attachment_import'):
            # No attachments, or the message was created in application code, so don't do anything.
            return super()._message_post_after_hook(new_message, message_values)

        files_data = self._to_files_data(attachments)

        # Extract embedded files. Note that `_unwrap_attachments` may create ir.attachment records - for example
        # see l10n_{es,it}_edi, so to retrieve those attachments you should use the `_from_files_data` method.
        files_data.extend(self._unwrap_attachments(files_data))

        # Dispatch the attachments into groups, and create a new invoice for each group beyond the first.
        valid_files_data = []
        extra_files_data = []
        for file_data in files_data:
            if self._should_attach_to_record(file_data['attachment']) or file_data['xml_tree'] is not None:
                valid_files_data.append(file_data)
            else:
                extra_files_data.append(file_data)

        if self.env.context.get('from_alias'):
            # This is a newly-created invoice from a mail alias.
            file_data_groups = self._group_files_data_into_groups_of_mixed_types(valid_files_data) or [[]]
            invoices = self
            if len(file_data_groups) > 1:
                create_vals = (len(file_data_groups) - 1) * self.copy_data()
                invoices |= self.with_context(skip_is_manually_modified=True).create(create_vals)

            for invoice, file_data_group in zip(invoices, file_data_groups):
                attachment_records = self._from_files_data(file_data_group)
                if invoice == self:
                    attachment_records |= self._from_files_data(extra_files_data)
                    new_message.attachment_ids = [Command.set(attachment_records.ids)]
                    message_values['attachment_ids'] = [Command.link(attachment.id) for attachment in attachment_records]
                    res = super()._message_post_after_hook(new_message, message_values)
                else:
                    sub_new_message = new_message.copy({
                        'res_id': invoice.id,
                        'attachment_ids': [Command.set(attachment_records.ids)],
                    })
                    sub_message_values = {
                        **message_values,
                        'res_id': invoice.id,
                        'attachment_ids': [Command.link(attachment.id) for attachment in attachment_records],
                    }
                    super(AccountMove, invoice)._message_post_after_hook(sub_new_message, sub_message_values)
                invoice._fix_attachments_on_record_from_files_data(file_data_group, extra_files_data)

            for invoice, file_data_group in zip(invoices, file_data_groups):
                if file_data_group:
                    invoice._extend_with_attachments(file_data_group, new=True)

            return res

        else:
            # This is an existing invoice on which a message was posted either by e-mail or via the webclient.
            attachment_records = self._from_files_data(files_data)
            self._fix_attachments_on_record_from_files_data(valid_files_data, extra_files_data)
            # Only trigger decoding if the message was sent by an active internal user (note OdooBot is always inactive).
            if self.env.user.active and self.env.user._is_internal():
                self._extend_with_attachments(files_data)

            new_message.attachment_ids = [Command.set(attachment_records.ids)]
            message_values['attachment_ids'] = [Command.link(attachment.id) for attachment in attachment_records]
            return super()._message_post_after_hook(new_message, message_values)