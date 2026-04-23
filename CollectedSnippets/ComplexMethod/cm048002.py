def _compute_l10n_es_edi_verifactu_warning(self):
        for move in self:
            last_document = move.l10n_es_edi_verifactu_document_ids.sorted()[:1]

            warning = False
            warning_level = False
            if last_document.state == 'registered_with_errors':
                warning = last_document.errors
                warning_level = 'warning'
            elif last_document.errors:
                warning = last_document.errors
                warning_level = 'danger'
            elif move.state == 'draft':
                if move.l10n_es_edi_verifactu_state:
                    warning = _("You are modifying a journal entry for which a Veri*Factu document has been sent to the AEAT already.")
                    warning_level = 'warning'
                elif last_document._filter_waiting():
                    warning = _("You are modifying a journal entry for which a Veri*Factu document is waiting to be sent.")
                    warning_level = 'warning'

            if last_document._filter_waiting():
                warning = _("%(existing_warning)sA Veri*Factu document is waiting to be sent as soon as possible.",
                            existing_warning=(warning + '\n' if warning else ''))
                warning_level = warning_level or 'info'

            move.l10n_es_edi_verifactu_warning = warning
            move.l10n_es_edi_verifactu_warning_level = warning_level