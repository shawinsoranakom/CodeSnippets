def _get_customer_information(self):
        email_normalized_to_values = super()._get_customer_information()

        for lead in self:
            email_key = lead.email_normalized or lead.email_from
            values = email_normalized_to_values.setdefault(email_key, {})
            values['lang'] = values.get('lang') or lead.lang_code
            values['name'] = values.get('name') or lead.customer_name or parse_contact_from_email(lead.email_from)[0] or lead.email_from
            values['phone'] = values.get('phone') or lead.phone
        return email_normalized_to_values