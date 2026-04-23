def _l10n_ro_edi_process_bill_messages(self, received_bills_messages):
        ''' Create bill received on the SPV, it it does not already exists.
        '''
        # Search potential similar bills: similar bills either:
        # - have an index that is present in the message data or,
        # - the same amount and seller VAT, and optionally the same bill date
        domain = (
            Domain('company_id', '=', self.env.company.id)
            & Domain('move_type', 'in', self.get_purchase_types())
            & (
                (
                    Domain('l10n_ro_edi_index', '=', False)
                    & Domain('l10n_ro_edi_state', '=', False)
                    & Domain.OR([
                        Domain('amount_total', '=', message['answer']['invoice']['amount_total'])
                        & Domain('commercial_partner_id.vat', '=', message['answer']['invoice']['seller_vat'])
                        & Domain('invoice_date', 'in', [message['answer']['invoice']['date'], False])
                        for message in received_bills_messages
                        if 'error' not in message['answer']
                    ])
                )
                | (
                    Domain('l10n_ro_edi_index', 'in', [message['id_solicitare'] for message in received_bills_messages])
                    & Domain('l10n_ro_edi_state', '=', 'invoice_validated')
                )
            )
        )
        similar_bills = self.env['account.move'].search(domain)

        indexed_similar_bills = similar_bills.filtered('l10n_ro_edi_index').mapped('l10n_ro_edi_index')
        non_indexed_similar_bills_dict = {
            (bill.commercial_partner_id.vat, bill.amount_total, bill.invoice_date): bill
            for bill in similar_bills
            if not bill.l10n_ro_edi_index
        }

        for message in received_bills_messages:
            if 'error' in message['answer']:
                continue

            if message['id_solicitare'] in indexed_similar_bills:
                # A bill with the same SPV index was already imported, skip it as we don't want it twice.
                continue

            # Create new bills if they don't already exist, else update their content
            bill = non_indexed_similar_bills_dict.get(
                (message['answer']['invoice']['seller_vat'], float(message['answer']['invoice']['amount_total']), message['answer']['invoice']['date'])
            )
            if not bill:
                bill = non_indexed_similar_bills_dict.get(
                (message['answer']['invoice']['seller_vat'], float(message['answer']['invoice']['amount_total']), False)
            )
            if not bill:
                bill = self.env['account.move'].create({
                'company_id': self.env.company.id,
                'move_type': 'in_invoice',
                'journal_id': self.env.company.l10n_ro_edi_anaf_imported_inv_journal_id.id,
            })

            bill.l10n_ro_edi_index = message['id_solicitare']

            self.env['l10n_ro_edi.document'].sudo().create({
                'invoice_id': bill.id,
                'state': 'invoice_validated',
                'key_download': message['id'],
                'key_signature': message['answer']['signature']['key_signature'],
                'key_certificate': message['answer']['signature']['key_certificate'],
                'attachment': base64.b64encode(message['answer']['signature']['attachment_raw']),
            })
            xml_attachment_raw = message['answer']['invoice']['attachment_raw']
            xml_attachment_id = self.env['ir.attachment'].sudo().create({
                'name': f"ciusro_{message['answer']['invoice']['name'].replace('/', '_')}.xml",
                'raw': xml_attachment_raw,
                'res_model': 'account.move',
                'res_id': bill.id,
            }).id
            files_data = self._to_files_data(self.env['ir.attachment'].browse(xml_attachment_id))
            bill._extend_with_attachments(files_data)
            chatter_message = self.env._("Synchronized with SPV from message %s", message['id'])
            if (bill.message_main_attachment_id.mimetype or '') != 'application/pdf':
                pdf = _request_ciusro_xml_to_pdf(self.env.company, xml_attachment_raw)
                if 'error' in pdf:
                    bill.message_post(body=self.env._(
                    "It was not possible to retrieve the PDF from the SPV for the following reason: %s",
                    pdf['error']
                    ))
                else:
                    pdf_attachment_id = self.env['ir.attachment'].sudo().create({
                        'name': f"ciusro_{message['answer']['invoice']['name'].replace('/', '_')}.pdf",
                        'raw': pdf['content'],
                        'res_model': 'account.move',
                        'res_id': bill.id,
                    }).id
                    bill.message_main_attachment_id = pdf_attachment_id
                    chatter_message += Markup("<br/>%s") % self.env._("No PDF found: PDF imported from SPV.")
            bill.message_post(body=chatter_message)