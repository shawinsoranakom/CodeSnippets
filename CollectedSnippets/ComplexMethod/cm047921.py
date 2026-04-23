def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **kwargs,
    ):
        """ Validate the address values and return the invalid fields, the missing fields, and any
        error messages.

        :param dict address_values: The address values to validates.
        :param res.partner partner_sudo: The partner whose address values to validate, if any (can
                                         be empty).
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param bool use_delivery_as_billing: Whether the provided address should be used as both the billing and
                              the delivery address.
        :param str required_fields: The additional required address values, as a comma-separated
                                    list of `res.partner` fields.
        :param dict kwargs: Extra form data, available for overrides and some method calls.
        :return: The invalid fields, the missing fields, and any error messages.
        :rtype: tuple[set, set, list]
        """
        # data: values after preprocess
        invalid_fields = set()
        missing_fields = set()
        error_messages = []

        if partner_sudo:
            name_change = (
                'name' in address_values
                and partner_sudo.name
                and address_values['name'] != partner_sudo.name.strip()
            )
            country_change = (
                'country_id' in address_values
                and partner_sudo.country_id
                and address_values['country_id'] != partner_sudo.country_id.id
            )
            email_change = (
                'email' in address_values
                and partner_sudo.email
                and address_values['email'] != partner_sudo.email
            )

            # Prevent changing the partner country if documents have been issued.
            if country_change and not partner_sudo._can_edit_country():
                invalid_fields.add('country_id')
                error_messages.append(_(
                    "Changing your country is not allowed once document(s) have been issued for your"
                    " account. Please contact us directly for this operation."
                ))

            # Prevent changing the partner name or email if it is an internal user.
            if (name_change or email_change) and not all(partner_sudo.user_ids.mapped('share')):
                if name_change:
                    invalid_fields.add('name')
                if email_change:
                    invalid_fields.add('email')
                error_messages.append(_(
                    "If you are ordering for an external person, please place your order via the"
                    " backend. If you wish to change your name or email address, please do so in"
                    " the account settings or contact your administrator."
                ))

            # Prevent changing commercial fields on sub-addresses, as they are expected to match
            # commercial partner values, and would be reset if modified on the commercial partner.
            if not (is_commercial_address := partner_sudo == partner_sudo.commercial_partner_id):
                for commercial_field_name in partner_sudo._commercial_fields():
                    if commercial_field_name not in address_values:
                        continue
                    partner_sudo_field = partner_sudo._fields[commercial_field_name]
                    partner_sudo_value = partner_sudo_field.convert_to_cache(
                        partner_sudo[commercial_field_name],
                        partner_sudo,
                    )
                    if (
                        partner_sudo_value != address_values[commercial_field_name]
                        and (
                            bool(partner_sudo_value)
                            or bool(address_values[commercial_field_name])
                        )
                    ):
                        invalid_fields.add(commercial_field_name)
                        field_description = partner_sudo_field._description_string(request.env)
                        if partner_sudo.commercial_partner_id.is_company:
                            error_messages.append(_(
                                "The %(field_name)s is managed on your company account.",
                                field_name=field_description,
                            ))
                        else:
                            error_messages.append(_(
                                "The %(field_name)s is managed on your main account address.",
                                field_name=field_description,
                            ))
                    else:
                        address_values.pop(commercial_field_name, None)

                # Company name shouldn't be updated anywhere but the main and company address, even
                # if it's not in the fields returned by _commercial_fields.
                if partner_sudo != request.env['res.partner']._get_current_partner(**kwargs):
                    address_values.pop('company_name', None)
            # Prevent changing the VAT number on a commercial partner if documents have been issued.
            elif (
                'vat' in address_values
                and partner_sudo.vat
                and address_values['vat'] != partner_sudo.vat
                and not partner_sudo.can_edit_vat()
            ):
                invalid_fields.add('vat')
                error_messages.append(_(
                    "Changing VAT number is not allowed once document(s) have been issued for your"
                    " account. Please contact us directly for this operation."
                ))
        else:
            # We're creating a new address, it'll only be the main address of public customers
            is_commercial_address = not request.env['res.partner']._get_current_partner(**kwargs)

        # Validate the email.
        if address_values.get('email') and not single_email_re.match(address_values['email']):
            invalid_fields.add('email')
            error_messages.append(_("Invalid Email! Please enter a valid email address."))

        # Validate the VAT number.
        ResPartnerSudo = request.env['res.partner'].sudo()
        if (
            address_values.get('vat')
            and hasattr(ResPartnerSudo, '_check_vat')  # account module is installed
            and 'vat' not in invalid_fields
        ):
            partner_dummy = ResPartnerSudo.new({
                fname: address_values[fname]
                for fname in self._get_vat_validation_fields()
                if fname in address_values
            })
            try:
                partner_dummy._check_vat()
            except ValidationError as exception:
                invalid_fields.add('vat')
                error_messages.append(exception.args[0])

        # Build the set of required fields from the address form's requirements.
        required_field_set = {f for f in required_fields.split(',') if f}

        # Complete the set of required fields based on the address type.
        country_id = address_values.get('country_id')
        country = request.env['res.country'].browse(country_id)
        if address_type == 'delivery' or use_delivery_as_billing:
            required_field_set |= self._get_mandatory_delivery_address_fields(country)
        if address_type == 'billing' or use_delivery_as_billing:
            required_field_set |= self._get_mandatory_billing_address_fields(country)
            if not is_commercial_address:
                commercial_fields = ResPartnerSudo._commercial_fields()
                for fname in commercial_fields:
                    if fname in required_field_set and fname not in address_values:
                        required_field_set.remove(fname)

        address_fields = self._get_mandatory_address_fields(country)
        if any(address_values.get(fname) for fname in address_fields):
            # If the customer provided any address information, they should provide their whole
            # address, even if the address wasn't required (e.g. the order only contains services).
            required_field_set |= address_fields

        # Verify that no required field has been left empty.
        for field_name in required_field_set:
            if not address_values.get(field_name):
                missing_fields.add(field_name)
        if missing_fields:
            error_messages.append(_("Some required fields are empty."))

        return invalid_fields, missing_fields, error_messages