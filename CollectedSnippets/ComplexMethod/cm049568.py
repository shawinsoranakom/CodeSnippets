def insert_record(self, request, model_sudo, values, custom, meta=None):
        if not model_sudo.env.su:
            raise ValueError("model_sudo should get passed with sudo")
        model_name = model_sudo.model
        if model_name == 'mail.mail':
            email_from = _('"%(company)s form submission" <%(email)s>', company=request.env.company.name, email=request.env.company.email)
            values.update({'reply_to': values.get('email_from'), 'email_from': email_from})
        record = request.env[model_name].with_user(SUPERUSER_ID).with_context(
            mail_create_nosubscribe=True,
        ).create(values)

        if custom or meta:
            _custom_label = "%s\n___________\n\n" % _("Other Information:")  # Title for custom fields
            if model_name == 'mail.mail':
                _custom_label = "%s\n___________\n\n" % _("This message has been posted on your website!")
            default_field = model_sudo.website_form_default_field_id
            default_field_data = values.get(default_field.name, '')
            custom_content = (default_field_data + "\n\n" if default_field_data else '') \
                + (_custom_label + custom + "\n\n" if custom else '') \
                + (self._meta_label + "\n________\n\n" + meta if meta else '')

            # If there is a default field configured for this model, use it.
            # If there isn't, put the custom data in a message instead
            if default_field.name:
                if default_field.ttype == 'html' or model_name == 'mail.mail':
                    custom_content = nl2br(custom_content)
                record.update({default_field.name: custom_content})
            elif hasattr(record, '_message_log'):
                record._message_log(
                    body=nl2br_enclose(custom_content, 'p'),
                    message_type='comment',
                )

        return record.id