def _prepare_address_form_values(
        self, partner_sudo, address_type='billing', use_delivery_as_billing=False, callback='', **kwargs
    ):
        """Prepare the rendering values of the address form.

        :param partner_sudo: The partner whose address to update through the address form.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param bool use_delivery_as_billing: Whether the provided address should be used as both the
                                             billing and the delivery address.
        :param str callback: The URL to redirect to in case of successful address creation/update.
        :param dict kwargs: additional parameters, forwarded to other methods as well.
        :return: The address page values.
        :rtype: dict
        """
        current_partner = request.env['res.partner']._get_current_partner(**kwargs)
        commercial_partner = current_partner.commercial_partner_id  # handling commercial fields

        # TODO in the future: rename can_edit_vat
        # Means something like 'can edit commercial fields on current address'
        if partner_sudo:
            # Existing address, use the values defined on the address
            state_id = partner_sudo.state_id.id
            country_sudo = partner_sudo.country_id
            can_edit_vat = partner_sudo.can_edit_vat()
        else:
            # New address, take default values from current partner
            country_sudo = current_partner.country_id or self._get_default_country(**kwargs)
            state_id = current_partner.state_id.id
            can_edit_vat = not current_partner or (
                partner_sudo == current_partner and current_partner.can_edit_vat()
            )
        address_fields = (country_sudo and country_sudo.get_address_fields()) or ['city', 'zip']

        return {
            'partner_sudo': partner_sudo,  # If set, customer is editing an existing address
            'partner_id': partner_sudo.id,
            'current_partner': current_partner,
            'commercial_partner': current_partner.commercial_partner_id,
            'is_commercial_address': not current_partner or partner_sudo == commercial_partner,
            'is_main_address': not current_partner or (partner_sudo and partner_sudo == current_partner),
            'commercial_address_update_url': (
                # Only redirect to account update if the logged in user is their own commercial
                # partner.
                current_partner == commercial_partner and "/my/account?redirect=/my/addresses"
            ),
            'address_type': address_type,
            'can_edit_vat': can_edit_vat,
            'can_edit_country': not partner_sudo.country_id or partner_sudo._can_edit_country(),
            'callback': callback,
            'country': country_sudo,
            'countries': request.env['res.country'].sudo().search([]),
            'is_used_as_billing': address_type == 'billing' or use_delivery_as_billing,
            'use_delivery_as_billing': use_delivery_as_billing,
            'state_id': state_id,
            'country_states': country_sudo.state_ids,
            'zip_before_city': (
                'zip' in address_fields
                and address_fields.index('zip') < address_fields.index('city')
            ),
            'vat_label': request.env._("VAT"),
            'discard_url': callback or '/my/addresses',
        }