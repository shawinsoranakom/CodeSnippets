def _compute_l10n_in_gst_treatment(self):
        for invoice in self.filtered(lambda m: m.country_code == 'IN' and m.state == 'draft'):
            partner = invoice.partner_id
            invoice.l10n_in_gst_treatment = (
                partner.l10n_in_gst_treatment
                or (
                    'overseas' if partner.country_id and partner.country_id.code != 'IN'
                    else partner.check_vat_in(partner.vat) and 'regular' or 'consumer'
                )
            )