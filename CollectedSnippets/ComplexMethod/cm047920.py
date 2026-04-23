def _parse_form_data(self, form_data):
        """ Parse the form data and return them converted into address values and extra form data.

        :param dict form_data: The form data to convert to address values.
        :return: A tuple of converted address values and extra form data.
        :rtype: tuple[dict, dict]
        """
        address_values = {}
        extra_form_data = {}

        ResPartner = request.env['res.partner']
        partner_fields = ResPartner._fields
        authorized_partner_fields = request.env['res.partner']._get_frontend_writable_fields()
        for key, value in form_data.items():
            if isinstance(value, str):
                value = value.strip()
            if key in partner_fields and key in authorized_partner_fields:
                field = partner_fields[key]
                if field.type == 'many2one' and isinstance(value, str) and value.isdigit():
                    address_values[key] = field.convert_to_cache(int(value), ResPartner)
                else:
                    # Always keep field values, even if falsy, as it might be for resetting a field.
                    address_values[key] = field.convert_to_cache(value, ResPartner)
            elif value:  # The value cannot be saved on the `res.partner` model.
                extra_form_data[key] = value

        if 'zipcode' in form_data and not form_data.get('zip'):
            address_values['zip'] = form_data.pop('zipcode', '')

        return address_values, extra_form_data