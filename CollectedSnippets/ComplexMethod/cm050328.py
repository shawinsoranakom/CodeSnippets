def _l10n_it_edi_base_export_check(self):
        def build_error(message, records):
            return {
                'message': message,
                **({
                    'action_text': _("View invoice(s)"),
                    'action': records._get_records_action(name=_("Invoice(s) to check")),
                } if len(self) > 1 else {})
            }

        errors = {}
        if moves := self.filtered(lambda move: move.l10n_it_edi_is_self_invoice and move._l10n_it_edi_services_or_goods() == 'both'):
            errors['l10n_it_edi_move_rc_mixed_product_types'] = build_error(
                message=_("Cannot apply Reverse Charge to bills which contains both services and goods."),
                records=moves)

        if pa_moves := self.filtered(lambda move: move.commercial_partner_id._l10n_it_edi_is_public_administration()):
            if moves := pa_moves.filtered(lambda move: not move.l10n_it_origin_document_type):
                message = _("Partner(s) belongs to the Public Administration, please fill out Origin Document Type field in the Electronic Invoicing tab.")
                errors['move_missing_origin_document'] = build_error(message=message, records=moves)
            if moves := pa_moves.filtered(lambda move: move.l10n_it_origin_document_date and move.l10n_it_origin_document_date > fields.Date.today()):
                message = _("The Origin Document Date cannot be in the future.")
                errors['l10n_it_edi_move_future_origin_document_date'] = build_error(message=message, records=moves)
        if pa_moves := self.filtered(lambda move: len(move.commercial_partner_id.l10n_it_pa_index or '') == 7):
            if moves := pa_moves.filtered(lambda move: not move.l10n_it_origin_document_type and (move.l10n_it_cig or move.l10n_it_cup)):
                message = _("CIG/CUP fields of partner(s) are present, please fill out Origin Document Type field in the Electronic Invoicing tab.")
                errors['move_missing_origin_document_field'] = build_error(message=message, records=moves)
        return errors