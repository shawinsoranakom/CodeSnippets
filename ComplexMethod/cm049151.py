def insert_record(self, request, model_sudo, values, custom, meta=None):
        is_lead_model = model_sudo.model == 'crm.lead'
        if is_lead_model:
            values_email_normalized = tools.email_normalize(values.get('email_from'))
            visitor_sudo = request.env['website.visitor']._get_visitor_from_request(force_create=True)
            visitor_partner = visitor_sudo.partner_id
            if values_email_normalized and visitor_partner and visitor_partner.email_normalized == values_email_normalized:
                # Here, 'phone' in values has already been formatted, see _handle_website_form.
                values_phone = values.get('phone')
                # We write partner id on crm only if no phone exists on partner or in input,
                # or if both numbers (after formating) are the same. This way we get additional phone
                # if possible, without modifying an existing one. (see inverse function on model crm.lead)
                if values_phone and visitor_partner.phone:
                    if values_phone == visitor_partner.phone:
                        values['partner_id'] = visitor_partner.id
                    elif (visitor_partner._phone_format('phone') or visitor_partner.phone) == values_phone:
                        values['partner_id'] = visitor_partner.id
                else:
                    values['partner_id'] = visitor_partner.id
            if 'company_id' not in values:
                values['company_id'] = request.website.company_id.id
            lang = request.env.context.get('lang', False)
            values['lang_id'] = values.get('lang_id') or request.env['res.lang']._get_data(code=lang).id

        result = super().insert_record(request, model_sudo, values, custom, meta=meta)

        if is_lead_model and visitor_sudo and result:
            lead_sudo = request.env['crm.lead'].browse(result).sudo()
            if lead_sudo.exists():
                vals = {'lead_ids': [(4, result)]}
                if not visitor_sudo.lead_ids and not visitor_sudo.partner_id:
                    vals['name'] = lead_sudo.contact_name
                visitor_sudo.write(vals)
        return result