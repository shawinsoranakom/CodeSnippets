def insert_record(self, request, model_sudo, values, custom, meta=None):
        model_name = model_sudo.model
        if model_name == 'project.task':
            visitor_sudo = request.env['website.visitor']._get_visitor_from_request()
            visitor_partner = visitor_sudo.partner_id
            if visitor_partner:
                values['partner_id'] = visitor_partner.id
            # When a task is created from the web editor, if the key 'user_ids' is not present, the user_ids is filled with the odoo bot. We set it to False to ensure it is not.
            values.setdefault('user_ids', False)

        res = super().insert_record(request, model_sudo, values, custom, meta=meta)
        if model_name != 'project.task':
            return res
        task = request.env['project.task'].sudo().browse(res)
        custom = custom.replace('email_from', _('Email'))
        custom_label = nl2br_enclose(_("Other Information"), 'h4')  # Title for custom fields
        default_field = model_sudo.website_form_default_field_id
        default_field_data = values.get(default_field.name, '')
        default_field_content = nl2br_enclose(html2plaintext(default_field_data), 'p')
        if default_field.name and default_field.name != 'description':
            default_field_content = nl2br_enclose(default_field.name.capitalize(), 'h4') + default_field_content
        custom_content = (default_field_content if default_field_data else '') \
                        + (custom_label + custom if custom else '') \
                        + (self._meta_label + meta if meta else '')

        if default_field.name:
            if default_field.ttype == 'html':
                custom_content = nl2br(custom_content)
            task[default_field.name] = custom_content
            task._message_log(
                body=custom_content,
                message_type='comment',
            )
        return res