def _validate_address_values(self, address_values, partner_sudo, address_type, *args, **kwargs):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values, partner_sudo, address_type, *args, **kwargs
        )

        if address_type == 'billing' and request.website.sudo().company_id.account_fiscal_country_id.code == 'TW' and request.website.sudo().company_id._is_ecpay_enabled():
            phone = address_values.get('phone')
            if phone:
                formatted_phone = request.env['account.move']._reformat_phone_number(phone)
                if not re.fullmatch(r'[\d]+', formatted_phone):
                    invalid_fields.add('phone')
                    error_messages.append(request.env._("Phone number contains invalid characters! It should be in the format: '+886 0997624293'."))
            if address_values.get('company_name'):  # B2B customer
                if not address_values.get('vat'):
                    missing_fields.add('vat')
                if not self._is_valid_tax_id(address_values.get('vat'), request.cart):
                    invalid_fields.add('vat')
                    error_messages.append(request.env._("Please enter a valid Tax ID"))

        return invalid_fields, missing_fields, error_messages