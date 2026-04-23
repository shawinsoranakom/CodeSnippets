def _compute_l10n_in_state_id(self):
        foreign_state = self.env.ref('l10n_in.state_in_oc', raise_if_not_found=False)
        for move in self:
            if move.country_code == 'IN' and move.is_sale_document(include_receipts=True):
                partner = (
                    move.partner_id.commercial_partner_id == move.partner_shipping_id.commercial_partner_id
                    and move.partner_shipping_id
                    or move.partner_id
                )
                if partner.country_id and partner.country_id.code != 'IN':
                    move.l10n_in_state_id = foreign_state
                    continue
                partner_state = partner.state_id or move.partner_id.commercial_partner_id.state_id or move.company_id.state_id
                country_code = partner_state.country_id.code or move.country_code
                move.l10n_in_state_id = partner_state if country_code == 'IN' else foreign_state
            elif move.country_code == 'IN' and move.journal_id.type == 'purchase':
                move.l10n_in_state_id = move.company_id.state_id
            else:
                move.l10n_in_state_id = False