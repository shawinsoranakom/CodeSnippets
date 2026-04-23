def _l10n_ro_edi_process_invoice_accepted_messages(self, sent_invoices_accepted_messages):
        ''' Process the validation messages of invoices sent

            It will also attempt to recover the original invoices, that are missing their index,
            by matching the name returned by the server and the one in the database.

            note: There is an edge case where 2 messages have the same invoice name but different indexes in
            their data; this could be due to a resequencing of the invoice and/or re-sending of an invoice. In
            that case coupled with name matching where none of the two invoices received an index, all signatures
            are added to the invoice; the user will have to manually update/select the correct one.

            For example: 2 invoices in the database
                - 11 already sent and should have gotten index AA, but did not receive it
                - 12 not sent
            Resequence them: 11->12 and 12->11
            Send new 11 that has not yet been sent, it should have gotten index AB but did not receive it.
            => In the messages, 2 invoices with name 11 and both index AA and AB.
        '''
        invoice_names = {message['answer']['invoice']['name'] for message in sent_invoices_accepted_messages if 'error' not in message['answer']}
        invoice_indexes = [message['id_solicitare'] for message in sent_invoices_accepted_messages]
        domain = (
            Domain('company_id', '=', self.env.company.id)
            & Domain('move_type', 'in', self.get_sale_types())
            & (
                (
                    Domain('l10n_ro_edi_index', 'in', invoice_indexes)
                    & Domain('l10n_ro_edi_state', '=', 'invoice_sent')
                )
                | (
                    Domain('name', 'in', list(invoice_names))
                    & Domain('l10n_ro_edi_index', '=', False)
                    & Domain('l10n_ro_edi_state', '=', 'invoice_not_indexed')
                )
            )
        )
        invoices = self.env['account.move'].search(domain)

        document_ids_to_delete = []
        index_to_move = {move.l10n_ro_edi_index: move for move in invoices}
        name_to_move = {move.name: move for move in invoices}
        for message in sent_invoices_accepted_messages:
            invoice = index_to_move.get(message['id_solicitare'])

            if not invoice:
                # The move related to the message does not have an index
                if 'error' in message['answer'] or not name_to_move.get(message['answer']['invoice']['name']):
                    continue

                # An invoice with the same name has been found
                invoice = name_to_move.get(message['answer']['invoice']['name'])

                # Update the index of invoices succesfully sent but without SPV indexes due to server
                # time-out for unknown reasons during the upload
                invoice.l10n_ro_edi_index = message['id_solicitare']
                invoice.l10n_ro_edi_state = 'invoice_sent'

            if 'error' in message['answer']:
                invoice.message_post(body=_(
                    "Error when trying to download the E-Factura data from the SPV: %s",
                    message['answer']['error']
                ))
                continue

            # Only delete invoice_sent documents and not all because one invoice can contain several signature due to
            # the edge case where 2 messages have the same invoice name but different indexes in their data; this could
            # be due to a resequencing of the invoice and/or re-sending of an invoice. In that case coupled with name
            # matching where none of the two invoices received an index, all signatures are added to the invoice; the
            # user will have to manually update/select the correct one.
            document_ids_to_delete += invoice.l10n_ro_edi_document_ids.filtered(lambda document: document.state == 'invoice_sent').ids

            invoice.message_post(body=_("This invoice has been accepted by the SPV."))
            self.env['l10n_ro_edi.document'].sudo().create({
                'invoice_id': invoice.id,
                'state': 'invoice_validated',
                'key_download': message['id'],
                'key_signature': message['answer']['signature']['key_signature'],
                'key_certificate': message['answer']['signature']['key_certificate'],
                'attachment': message['answer']['signature']['attachment_raw'],
            })

        self.env['l10n_ro_edi.document'].sudo().browse(document_ids_to_delete).unlink()