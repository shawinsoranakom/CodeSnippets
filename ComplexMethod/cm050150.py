def _validate_address_values(self, address_values, partner_sudo, address_type, *args, **kwargs):
        """ We extend the method to add a new validation. If ARCA Resposibility is:

        * Final Consumer or Foreign Customer: then it can select any identification type.
        * Any other (Monotributista, RI, etc): should select always "CUIT" identification type
        """
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values, partner_sudo, address_type, *args, **kwargs
        )

        # Identification type and ARCA Responsibility Combination
        if address_type == 'billing' and self._is_argentinean_company():
            if (missing_fields
                and (
                    'l10n_ar_afip_responsibility_type_id' in missing_fields
                    or 'l10n_latam_identification_type_id' in missing_fields
                )
            ):
                return invalid_fields, missing_fields, error_messages

            afip_resp = request.env['l10n_ar.afip.responsibility.type'].browse(
                address_values.get('l10n_ar_afip_responsibility_type_id')
            )
            id_type = request.env['l10n_latam.identification.type'].browse(
                address_values.get('l10n_latam_identification_type_id')
            )

            if not id_type or not afip_resp:
                # Those two values were not provided and are not required, skip the validation
                return invalid_fields, missing_fields, error_messages

            # Check if the ARCA responsibility is different from Final Consumer or Foreign Customer,
            # and if the identification type is different from CUIT
            if afip_resp.code not in ['5', '9'] and id_type != request.env.ref('l10n_ar.it_cuit'):
                invalid_fields.add('l10n_latam_identification_type_id')
                error_messages.append(request.env._(
                    "For the selected ARCA Responsibility you will need to set CUIT Identification Type"
                ))

        return invalid_fields, missing_fields, error_messages