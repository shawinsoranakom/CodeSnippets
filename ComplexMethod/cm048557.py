def assert_attachment_import(self, origin, attachments_vals, expected_invoices):
        """ Simulate the upload and import of one or more attachments and assert that the
            created attachments were linked to the expected messages and invoices.

            :param origin: The source from which the attachments came (see `_upload_and_import_attachments`).

            :param attachments_vals: A list of values representing the attachments to be uploaded to Odoo

            :param expected_invoices: a dict {
                invoice_index (int): {
                    filename: {
                        'on_invoice': (bool) whether it should be attached on the invoice,
                        'on_message': (bool) whether it should be attached to a message in the chatter,
                        'is_decoded': (bool) whether it should have been decoded on the invoice,
                        'is_new': (bool) whether the call to the decoder should have `new=True`
                    }
                }
            }

            which for each newly-created invoice indicates:
                (1) which of the files it should be linked to, and, for each file
                    (a) whether it should be attached to the invoice or merely to a message on the invoice.
                    (b) whether it should have been decoded on the invoice
        """
        # Because no decoders are defined in `account` itself, if we want to test the decoder flow we need
        # to define a fictional format that will be decoded, and patch the `_get_import_file_type`
        # and `_get_edi_decoder` methods to accept it.

        with self._patch_import_methods() as decoder_calls:
            created_attachments, created_messages, created_invoices = self._upload_and_import_attachments(origin, attachments_vals)

        # Check that no two attachments were created with the same filename (needed for the rest of the test to work properly)
        self.assertEqual(len(created_attachments), len(created_attachments.grouped('name')))

        # Construct a dict representing the way the attachments were linked to new invoices and messages.
        actual_invoices = {}

        for message in created_messages.filtered(lambda m: m.model == 'account.move'):
            for attachment in message.attachment_ids:
                actual_invoices.setdefault(message.res_id, {}).setdefault(attachment.name, {})['on_message'] = True

        for attachment in created_attachments:
            if attachment.res_model == 'account.move':
                actual_invoices.setdefault(attachment.res_id, {}).setdefault(attachment.name, {})['on_invoice'] = True

        for decoder_call in decoder_calls:
            invoice = decoder_call[0]
            filename = decoder_call[1]['name']
            actual_invoices.setdefault(invoice.id, {}).setdefault(filename, {})['is_decoded'] = True

            if decoder_call[2]:
                actual_invoices[invoice.id][filename]['is_new'] = True

        # Map the invoice IDs to the invoice indexes of the expected_invoices.
        index_by_invoice_id = {
            invoice_id: index
            for index, invoice_id in enumerate(created_invoices.mapped('id'), start=1)
        }
        actual_invoices = {
            index_by_invoice_id[invoice_id]: attachment_info
            for invoice_id, attachment_info in actual_invoices.items()
        }
        self.assertDictEqual(actual_invoices, expected_invoices)