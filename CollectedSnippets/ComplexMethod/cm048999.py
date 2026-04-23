def _get_recipient_values(self, partner, is_simplified=False):
        # TicketBAI accept recipient data for simplified invoices,
        # but only if the partner has a VAT number
        if is_simplified and not partner.vat:
            return {}
        recipient_values = {
            'partner': partner,
            'partner_address': ', '.join(filter(None, [partner.street, partner.street2, partner.city])),
            'alt_id_number': partner.vat or 'NO_DISPONIBLE',
        }

        if not partner._l10n_es_is_foreign() and partner.vat:
            recipient_values['nif'] = partner.vat[2:] if partner.vat.startswith('ES') else partner.vat

        elif partner.country_id and 'EU' in partner.country_id.country_group_codes:
            recipient_values['alt_id_type'] = '02'

        else:
            recipient_values['alt_id_type'] = '04' if partner.vat else '06'
            recipient_values['alt_id_country'] = partner.country_id.code if partner.country_id else None

        return {'recipient': recipient_values}