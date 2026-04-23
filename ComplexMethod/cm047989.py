def _get_lead_contact_values(self):
        """ Specific management of contact values. Rule creation basis has some
        effect on contact management

          * in attendee mode: keep registration partner only if partner phone and
            email match. Indeed lead are synchronized with their contact and it
            would imply rewriting on partner, and therefore on other documents;
          * in batch mode: if a customer is found use it as main contact. Registrations
            details are included in lead description;

        :returns: values used for create / write on a lead
        :rtype: dict
        """
        sorted_self = self.sorted("id")
        valid_partner = next(
            (reg.partner_id for reg in sorted_self if reg.partner_id != self.env.ref('base.public_partner')),
            self.env['res.partner']
        )  # CHECKME: broader than just public partner

        # mono registration mode: keep partner only if email and phone matches;
        # otherwise registration > partner. Note that email format and phone
        # formatting have to taken into account in comparison
        if len(self) == 1 and valid_partner:
            # compare emails: email_normalized or raw
            if self.email and valid_partner.email:
                if valid_partner.email_normalized and tools.email_normalize(self.email) != valid_partner.email_normalized:
                    valid_partner = self.env['res.partner']
                elif not valid_partner.email_normalized and valid_partner.email != self.email:
                    valid_partner = self.env['res.partner']

            # compare phone, taking into account formatting
            if valid_partner and self.phone and valid_partner.phone:
                phone_formatted = self._phone_format(fname='phone', country=valid_partner.country_id)
                partner_phone_formatted = valid_partner._phone_format(fname='phone')
                if phone_formatted and partner_phone_formatted and phone_formatted != partner_phone_formatted:
                    valid_partner = self.env['res.partner']
                if (not phone_formatted or not partner_phone_formatted) and self.phone != valid_partner.phone:
                    valid_partner = self.env['res.partner']

        registration_phone = sorted_self._find_first_notnull('phone')
        if valid_partner:
            contact_vals = self.env['crm.lead']._prepare_values_from_partner(valid_partner)
            # force email_from / phone only if not set on partner because those fields are now synchronized automatically
            if not valid_partner.email:
                contact_vals['email_from'] = sorted_self._find_first_notnull('email')
            if not valid_partner.phone:
                contact_vals['phone'] = registration_phone
        else:
            # don't force email_from + partner_id because those fields are now synchronized automatically
            contact_vals = {
                'contact_name': sorted_self._find_first_notnull('name'),
                'email_from': sorted_self._find_first_notnull('email'),
                'phone': registration_phone,
                'lang_id': False,
            }
        contact_name = valid_partner.name or sorted_self._find_first_notnull('name') or sorted_self._find_first_notnull('email')
        contact_vals.update({
            'name': f'{self.event_id[:1].name} - {contact_name}',
            'partner_id': valid_partner.id,
        })

        return contact_vals