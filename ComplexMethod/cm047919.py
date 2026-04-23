def _create_or_update_address(
        self,
        partner_sudo,
        address_type='billing',
        use_delivery_as_billing=False,
        callback='/my/addresses',
        required_fields=False,
        verify_address_values=True,
        **form_data
    ):
        """ Create or update an address if there is no error else return error dict.

        :param str partner_id: The partner whose address to update with the address form, if any.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param dict form_data: The form data to process as address values.
        :param str use_delivery_as_billing: Whether the provided address should be used as both the
                                            billing and the delivery address. 'true' or 'false'.
        :param str callback: The URL to redirect to in case of successful address creation/update.
        :param str required_fields: The additional required address values, as a comma-separated
                                    list of `res.partner` fields.
        :param bool verify_address_values: Whether we want to check the given address values.
        :return: Partner record and A JSON-encoded feedback, with either the success URL or
                 an error message.
        :rtype: res.partner, dict
        """
        use_delivery_as_billing = str2bool(use_delivery_as_billing or 'false')

        # Parse form data into address values, and extract incompatible data as extra form data.
        address_values, extra_form_data = self._parse_form_data(form_data)

        if verify_address_values:
            # Validate the address values and highlights the problems in the form, if any.
            invalid_fields, missing_fields, error_messages = self._validate_address_values(
                address_values,
                partner_sudo,
                address_type,
                use_delivery_as_billing,
                required_fields or '',
                **extra_form_data,
            )
            if error_messages:
                return partner_sudo, {
                    'invalid_fields': list(invalid_fields | missing_fields),
                    'messages': error_messages,
                }

        if not partner_sudo:  # Creation of a new address.
            self._complete_address_values(
                address_values, address_type, use_delivery_as_billing, **form_data
            )
            create_context = clean_context(request.env.context)
            create_context.update({
                'tracking_disable': True,
                'no_vat_validation': True,  # Already verified in _validate_address_values
            })
            partner_sudo = request.env['res.partner'].sudo().with_context(
                create_context
            ).create(address_values)
            if hasattr(partner_sudo, '_onchange_phone_validation'):
                # The `phone_validation` module is installed.
                partner_sudo._onchange_phone_validation()
        elif not self._are_same_addresses(address_values, partner_sudo):
            # If name is not changed then pop it from the address_values, as it affects the bank account holder name
            if address_values['name'].strip() == (partner_sudo.name or '').strip():
                address_values.pop('name')
            partner_sudo.write(address_values)  # Keep the same partner if nothing changed.
            if 'phone' in address_values and hasattr(partner_sudo, '_onchange_phone_validation'):
                # The `phone_validation` module is installed.
                partner_sudo._onchange_phone_validation()

        if (
            'company_name' in address_values
            and partner_sudo.commercial_partner_id != partner_sudo
            and partner_sudo.commercial_partner_id.is_company
        ):
            # If partner is an individual, update existing company's name or remove one
            company_name = address_values['company_name']
            parent_company = partner_sudo.commercial_partner_id
            partner_sudo.company_name = False

            if company_name and parent_company and parent_company.name != company_name:
                parent_company.name = company_name

        self._handle_extra_form_data(extra_form_data, address_values)

        return partner_sudo, {'redirectUrl': callback}