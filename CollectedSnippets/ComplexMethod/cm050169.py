def extract_data(self, model_sudo, values):
        data = super().extract_data(model_sudo, values)
        if model_sudo.model == 'project.task' and values.get('email_from'):
            partner = request.env['mail.thread'].sudo()._partner_find_from_emails_single([values['email_from']], no_create=True)
            data['record']['email_from'] = values['email_from']
            if partner:
                data['record']['partner_id'] = partner.id
                custom = [
                   (field, data['record'].pop(field))
                   for field in ['partner_name', 'partner_phone', 'partner_company_name']
                   if data['record'].get(field)
                ]
                data['custom'] += "\n" + "\n".join(["%s : %s" % c for c in custom])
            else:
                data['record']['email_cc'] = values['email_from']
                if values.get('partner_phone'):
                    data['record']['partner_phone'] = values['partner_phone']
                if values.get('partner_name'):
                    data['record']['partner_name'] = values['partner_name']
                if values.get('partner_company_name'):
                    data['record']['partner_company_name'] = values['partner_company_name']
        return data