def _call_web_service_before_invoice_pdf_render(self, invoices_data):
        # EXTENDS 'account'
        super()._call_web_service_before_invoice_pdf_render(invoices_data)

        for invoice, invoice_data in invoices_data.items():
            if 'es_verifactu' not in invoice_data['extra_edis']:
                continue
            vals = invoice._l10n_es_edi_verifactu_get_record_values()
            action = msg = None

            if vals['verifactu_move_type'] == 'correction_substitution' and not vals['substituted_document']:
                substituted_move = invoice.l10n_es_edi_verifactu_substituted_entry_id
                msg = _("There is no Veri*Factu document for the substituted record.")
                action = invoice._l10n_es_edi_verifactu_action_go_to_journal_entry(substituted_move)
            elif vals['verifactu_move_type'] == 'correction_substitution' and not vals['substituted_document_reversal_document']:
                substituted_move = invoice.l10n_es_edi_verifactu_substituted_entry_id
                msg = _("There is no Veri*Factu document for the reversal of the substituted record.")
                action = invoice._l10n_es_edi_verifactu_action_go_to_journal_entry(substituted_move.reversal_move_ids)
            elif vals['verifactu_move_type'] in ('correction_incremental', 'reversal_for_substitution') and not vals['refunded_document']:
                reversed_move = invoice.reversed_entry_id
                msg = _("There is no Veri*Factu document for the refunded record.")
                action = invoice._l10n_es_edi_verifactu_action_go_to_journal_entry(reversed_move)

            if action and msg:
                invoice_data['error'] = {
                    'verifactu_redirect_action': action,
                    'error_title': _("Go to the journal entry"),
                    'errors': [msg],
                }

        checked_invoices = self.env['account.move'].browse([
            invoice.id for invoice, invoice_data in invoices_data.items()
            if 'es_verifactu' in invoice_data['extra_edis'] and not invoice_data.get('error', {}).get('verifactu_redirect_action')
        ])
        invoices_to_send = self._l10n_es_edi_verifactu_get_move_info(checked_invoices)['moves_to_send']

        created_document = invoices_to_send._l10n_es_edi_verifactu_mark_for_next_batch()

        for invoice in invoices_to_send:
            if not created_document[invoice].chain_index:
                invoices_data[invoice]['error'] = {
                    'error_title': _("The Veri*Factu document could not be created for all invoices."),
                    'errors': [_("See the 'Veri*Factu' tab for more information.")],
                }

        if created_document and self._can_commit():
            self.env.cr.commit()