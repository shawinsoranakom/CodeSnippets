def _peppol_import_invoice(self, attachment, peppol_state, uuid, journal=None):
        """Save new documents in an accounting journal, when one is specified on the company.

        :param attachment: the new document
        :param peppol_state: the state of the received Peppol document
        :param uuid: the UUID of the Peppol document
        :param journal: journal to use for the new move (otherwise the company's peppol journal will be used)
        :return: the created move (if any)
        """
        self.ensure_one()

        file_data = self.env['account.move']._to_files_data(attachment)[0]

        # Self-billed invoices are invoices which your customer creates on your behalf and sends you via Peppol.
        # In this case, the invoice needs to be created as an out_invoice in a sale journal.
        # 329/527: Self-billing invoice; 261: Self-billing credit note
        is_self_billed = False
        if file_data['xml_tree'].findtext('.//{*}InvoiceTypeCode') in ['389', '527'] or file_data['xml_tree'].findtext('.//{*}CreditNoteTypeCode') == '261':
            is_self_billed = True

        if not is_self_billed:
            journal = journal or self.company_id.peppol_purchase_journal_id
            move_type = 'in_invoice'
            if not journal:
                return {}

        else:
            journal = (
                journal
                or self.env['account.journal'].search(
                    [
                        *self.env['account.journal']._check_company_domain(self.company_id),
                        ('type', '=', 'sale'),
                    ],
                    limit=1
                )
            )
            move_type = 'out_invoice'
            if not journal:
                return {}

        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'move_type': move_type,
            'peppol_move_state': peppol_state,
            'peppol_message_uuid': uuid,
        })
        if 'is_in_extractable_state' in move._fields:
            move.is_in_extractable_state = False

        try:
            move._extend_with_attachments([file_data], new=True)
            move._autopost_bill()
        except Exception:
            _logger.exception("Unexpected error occurred during the import of bill with id %s", move.id)
        attachment.write({'res_model': 'account.move', 'res_id': move.id})
        return {'uuid': uuid, 'move': move}