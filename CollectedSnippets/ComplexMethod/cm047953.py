def get_vat_data(partner, force_vat=None):
            if partner.country_code == 'HU' or force_vat:
                return {
                    'tax_number': partner.l10n_hu_group_vat or (force_vat or partner.vat),
                    'group_member_tax_number': partner.l10n_hu_group_vat and (force_vat or partner.vat),
                }
            elif partner.country_code in eu_country_codes:
                return {'community_vat_number': partner.vat}
            else:
                return {'third_state_tax_id': partner.vat}