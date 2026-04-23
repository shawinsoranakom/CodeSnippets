def show_ticket_validation_screen(self, access_token='', **kwargs):
        def _parse_additional_values(fields, prefix, kwargs):
            """ Parse the values in the kwargs by extracting the ones matching the given fields name.
            :return a dict with the parsed value and the field name as key, and another on with the prefix to
            re-render the form with previous values if needed.
            """
            res, res_prefixed = {}, {}
            for field in fields:
                key = prefix + field.name
                if key in kwargs:
                    val = kwargs.pop(key)
                    res[field.name] = val
                    res_prefixed[key] = val
            return res, res_prefixed

        # If the route is called directly, return a 404
        if not access_token:
            return request.not_found()
        # Get the order using the access token. We can't use the id in the route because we may not have it yet when the QR code is generated.
        pos_order = request.env['pos.order'].sudo().search([('access_token', '=', access_token)])
        if not pos_order:
            return request.not_found()

        # Set the proper context in case of unauthenticated user accessing
        # from the main company website
        pos_order = pos_order.with_company(pos_order.company_id).with_context(allowed_company_ids=pos_order.company_id.ids)

        # If the order was already invoiced, return the invoice directly by forcing the access token so that the non-connected user can see it.
        if pos_order.account_move and pos_order.account_move.is_sale_document():
            return request.redirect('/my/invoices/%s?access_token=%s' % (pos_order.account_move.id, pos_order.account_move._portal_ensure_token()))

        if not request.env['res.company']._with_locked_records(pos_order, allow_raising=False):
            return

        # Get the optional extra fields that could be required for a localisation.
        pos_order_country = pos_order.company_id.account_fiscal_country_id
        additional_partner_fields = request.env['res.partner'].get_partner_localisation_fields_required_to_invoice(pos_order_country)
        additional_invoice_fields = request.env['account.move'].get_invoice_localisation_fields_required_to_invoice(pos_order_country)

        user_is_connected = not request.env.user._is_public()

        # Validate the form by ensuring required fields are filled and the VAT is correct.
        form_values = {'extra_field_values': {}}
        partner = (user_is_connected and request.env.user.partner_id) or pos_order.partner_id
        if kwargs and request.httprequest.method == 'POST':
            form_values.update(kwargs)
            # Extract the additional fields values from the kwargs now as they can't be there when validating the 'regular' partner form.
            partner_values, prefixed_partner_values = _parse_additional_values(additional_partner_fields, 'partner_', kwargs)
            form_values['extra_field_values'].update(prefixed_partner_values)
            # Do the same for invoice values, separately as they are only needed for the invoice creation.
            invoice_values, prefixed_invoice_values = _parse_additional_values(additional_invoice_fields, 'invoice_', kwargs)
            form_values['extra_field_values'].update(prefixed_invoice_values)
            # Check the basic form fields if the user is not connected as we will need these information to create the new user.
            partner, feedback_dict = self._create_or_update_address(partner, **(kwargs | partner_values))
            form_values.update(feedback_dict)
            missing_fields, error_messages = self._validate_extra_form_details(
                partner_values | invoice_values,
                additional_partner_fields + additional_invoice_fields
            )
            form_values.update({
                'invalid_field': form_values.get('invalid_fields', []) + list(missing_fields),
                'messages': form_values.get('messages', []) + error_messages
            })
            if not form_values.get('invalid_fields'):
                return self._get_invoice(partner, invoice_values, pos_order, additional_invoice_fields, kwargs)

        elif user_is_connected:
            return self._get_invoice(partner, {}, pos_order, additional_invoice_fields, kwargs)

        # Most of the time, the country of the customer will be the same as the order. We can prefill it by default with the country of the company.
        if 'country' not in form_values:
            form_values['country'] = pos_order_country

        # Prefill the customer extra values if there is any and an user is connected
        if partner:
            if additional_partner_fields:
                form_values['extra_field_values'] = {'partner_' + field.name: partner[field.name] for field in additional_partner_fields if field.name not in form_values['extra_field_values']}

            # This is just to ensure that the user went and filled its information at least once.
            # Another more thorough check is done upon posting the form.
            if not partner.country_id or not partner.street:
                form_values['partner_address'] = False
            else:
                form_values['partner_address'] = partner._display_address()

        return request.render("point_of_sale.ticket_validation_screen", {
            **self._prepare_address_form_values(partner, **kwargs),
            'partner': partner,
            'address_url': f'/my/account?redirect=/pos/ticket/validate?access_token={access_token}',
            'user_is_connected': user_is_connected,
            'format_amount': format_amount,
            'env': request.env,
            'pos_order': pos_order,
            'invoice_required_fields': additional_invoice_fields,
            'partner_required_fields': additional_partner_fields,
            'access_token': access_token,
            'invoice_sending_methods': {'email': _("by Email")},
            **form_values,
        })