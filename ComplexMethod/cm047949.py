def _l10n_hu_edi_get_valid_actions(self):
        """ If any NAV 3.0 flows are applicable to the given invoice, return them, else None. """
        self.ensure_one()
        valid_actions = []
        if (
            self.country_code == 'HU'
            and self.is_sale_document()
            and self.state == 'posted'
        ):
            if self.l10n_hu_edi_state in [False, 'rejected', 'cancelled']:
                valid_actions.append('upload')
            if self.l10n_hu_edi_transaction_code:
                valid_actions.append('query_status')
            if self.l10n_hu_edi_state in ['confirmed', 'confirmed_warning']:
                valid_actions.append('request_cancel')
            if not valid_actions:
                # Placeholder to denote that the invoice was already processed with a NAV flow
                valid_actions.append(True)
        return valid_actions