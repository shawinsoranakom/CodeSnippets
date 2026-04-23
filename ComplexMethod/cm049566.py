def _handle_website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search([('model', '=', model_name), ('website_form_access', '=', True)])
        if not model_record:
            return json.dumps({
                'error': _("The form's specified model does not exist")
            })

        try:
            data = self.extract_data(model_record, kwargs)
        # If we encounter an issue while extracting data
        except ValidationError as e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields': e.args[0]})

        try:
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'])
                # in case of an email, we want to send it immediately instead of waiting
                # for the email queue to process

                if model_name == 'mail.mail':
                    form_has_email_cc = {'email_cc', 'email_bcc'} & kwargs.keys() or \
                        'email_cc' in kwargs["website_form_signature"]
                    # remove the email_cc information from the signature
                    kwargs["website_form_signature"] = kwargs["website_form_signature"].split(':')[0]
                    if kwargs.get("email_to"):
                        value = kwargs['email_to'] + (':email_cc' if form_has_email_cc else '')
                        hash_value = hmac(model_record.env, 'website_form_signature', value)
                        if not consteq(kwargs["website_form_signature"], hash_value):
                            raise AccessDenied(self.env._('invalid website_form_signature'))
                    request.env[model_name].sudo().browse(id_record).send()

        # Some fields have additional SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model_model'] = model_record.model
        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id'] = id_record

        return json.dumps({'id': id_record})