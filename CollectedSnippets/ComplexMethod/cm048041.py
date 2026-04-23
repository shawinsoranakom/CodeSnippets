def _get_l10n_in_edi_partner_details(
            self,
            partner,
            set_vat=True,
            set_phone_and_email=True,
            is_overseas=False,
            pos_state_id=False
    ):
        """
            Create the dictionary based partner details
            if set_vat is true then, vat(GSTIN) and legal name(LglNm) is added
            if set_phone_and_email is true then phone and email is add
            if set_pos is true then state code from partner
             or passed state_id is added as POS(place of supply)
            if is_overseas is true then pin is 999999 and GSTIN(vat) is URP and Stcd is .
            if pos_state_id is passed then we use set POS
        """
        zip_digits = self._l10n_in_extract_digits(partner.zip)
        partner_details = {
            'Addr1': partner.street or '',
            'Loc': partner.city or '',
            'Pin': zip_digits and int(zip_digits) or '',
            'Stcd': partner.state_id.l10n_in_tin or '',
        }
        if partner.street2 and re.match(r"^.{3,100}$", partner.street2):
            partner_details['Addr2'] = partner.street2
        if set_phone_and_email:
            if (
                partner.email
                and re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", partner.email)
                and re.match(r"^.{6,100}$", partner.email)
            ):
                partner_details['Em'] = partner.email
            if (
                partner.phone
                and re.match(r"^[0-9]{10,12}$", self._l10n_in_extract_digits(partner.phone))
            ):
                partner_details['Ph'] = self._l10n_in_extract_digits(partner.phone)
        if pos_state_id:
            partner_details['POS'] = pos_state_id.l10n_in_tin or ''
        if set_vat:
            partner_details.update({
                'LglNm': partner.commercial_partner_id.name,
                'GSTIN': partner.vat or 'URP',
            })
        else:
            partner_details['Nm'] = partner.name
        # For no country I would suppose it is India, so not sure this is super right
        if is_overseas and (not partner.country_id or partner.country_id.code != 'IN'):
            partner_details.update({
                "GSTIN": "URP",
                "Pin": 999999,
                "Stcd": "96",
                "POS": "96",
            })
        return partner_details