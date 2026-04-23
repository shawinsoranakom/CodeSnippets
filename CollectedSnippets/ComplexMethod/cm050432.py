def _get_customer_information(self):
        email_keys_to_values = super()._get_customer_information()

        for lead in self:
            email_key = lead.email_normalized or lead.email_from
            # do not fill Falsy with random data, unless monorecord (= always correct)
            if not email_key and len(self) > 1:
                continue
            values = email_keys_to_values.setdefault(email_key, {})
            contact_name = lead.contact_name or parse_contact_from_email(lead.email_from)[0] or lead.email_from
            is_company = bool(lead.partner_name) and contact_name == lead.partner_name
            # Note that we don't attempt to create the parent company even if partner name is set
            values.update({
                key: val for key, val in lead._prepare_customer_values(
                    contact_name, is_company=is_company, parent_id=False
                ).items() if val and key != 'email'  # don't force email used as criterion
            })
            values['is_company'] = is_company
            if not is_company and lead.commercial_partner_id:
                values['parent_id'] = lead.commercial_partner_id.id
                values.pop('company_name', None)
        return email_keys_to_values