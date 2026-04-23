def l10n_es_tbai_cancel(self):
        for invoice in self:
            if invoice.inalterable_hash:
                raise UserError(_('You cannot reset to draft a locked journal entry.'))
            invoice._l10n_es_tbai_lock_move()

            if invoice.l10n_es_tbai_cancel_document_id and invoice.l10n_es_tbai_cancel_document_id.state == 'rejected':
                invoice.l10n_es_tbai_cancel_document_id.sudo().unlink()

            if not invoice.l10n_es_tbai_cancel_document_id:
                invoice.l10n_es_tbai_cancel_document_id = invoice._l10n_es_tbai_create_edi_document(cancel=True)

            edi_document = invoice.l10n_es_tbai_cancel_document_id

            error = edi_document._post_to_web_service(invoice._l10n_es_tbai_get_values(cancel=True))
            if error:
                raise UserError(error)

            if edi_document.state == 'accepted':
                invoice.button_cancel()
                invoice._l10n_es_tbai_post_document_in_chatter(edi_document.response_message, cancel=True)

            if self.env['account.move.send']._can_commit():
                self.env.cr.commit()

            if edi_document.state != 'accepted':
                raise UserError(edi_document.response_message)