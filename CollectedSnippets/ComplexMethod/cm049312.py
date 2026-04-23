def _l10n_ro_edi_stock_validate_data(self, data: dict):
        errors = []

        # API access token
        if not data['company_id'].l10n_ro_edi_access_token:
            errors.append(_('Romanian access token not found. Please generate or fill it in the settings.'))

        # carrier partner fields
        partner = data['transport_partner_id']
        missing_carrier_partner_fields = []

        if not partner.vat:
            missing_carrier_partner_fields.append(_("VAT"))

        if not partner.city:
            missing_carrier_partner_fields.append(_("City"))

        if not partner.street:
            missing_carrier_partner_fields.append(_("Street"))

        if len(missing_carrier_partner_fields) == 1:
            errors.append(_("The delivery carrier partner is missing the %(field_name)s field.", field_name=missing_carrier_partner_fields[0]))
        elif len(missing_carrier_partner_fields) > 1:
            errors.append(_("The delivery carrier partner is missing following fields: %(field_names)s", field_names=', '.join(missing_carrier_partner_fields)))

        # operation type
        if not data['l10n_ro_edi_stock_operation_type']:
            errors.append(_("Operation type is missing."))
            return errors  # return prematurely because a lot of fields depend on the operation type

        # operation scope
        if not data['l10n_ro_edi_stock_operation_scope']:
            errors.append(_("Operation scope is missing."))

        # vehicle & trailer numbers
        if not data['l10n_ro_edi_stock_vehicle_number']:
            errors.append(_("Vehicle number is missing."))

        # All filled-in vehicle and trailer numbers must be unique
        license_plates = [num for num in (data['l10n_ro_edi_stock_vehicle_number'], data['l10n_ro_edi_stock_trailer_1_number'], data['l10n_ro_edi_stock_trailer_2_number']) if num]
        if len(license_plates) != len(set(license_plates)):
            errors.append(_("Vehicle number and trailer number fields must be unique."))

        # rate codes
        if 'intrastat_code_id' in self.env['product.product']._fields and data['l10n_ro_edi_stock_operation_type'] not in ('60', '70'):
            product_without_code_names = {move_line.product_id.name
                                          for move in data['stock_move_ids']
                                          for move_line in move.move_line_ids
                                          if not move_line.product_id.intrastat_code_id.code}

            if product_without_code_names:
                if len(product_without_code_names) == 1:
                    (product_name,) = product_without_code_names
                    errors.append(_("Product %(name)s is missing the intrastat code value.", name=product_name))
                else:
                    errors.append(_("Products %(names)s are missing the intrastat code value.", names=", ".join(product_without_code_names)))

        # Location types
        if not data['l10n_ro_edi_stock_start_loc_type']:
            if not data['l10n_ro_edi_stock_end_loc_type']:
                errors.append(_("Both 'End' and 'Start Location Type' are missing"))
            else:
                errors.append(_("'Start Location Type' is missing"))

            return errors  # return prematurely because all the start location fields depend on this field

        if not data['l10n_ro_edi_stock_end_loc_type']:
            errors.append(_("'End Location Type' is missing"))
            return errors  # return prematurely because all the end location fields depend on this field

        # Location fields
        for location in ('start', 'end'):
            loc_value = data[f'l10n_ro_edi_stock_{location}_loc_type']
            loc_group = _("'Start Location'") if location == 'start' else _("'End Location'")

            if loc_value == 'bcp' and not data[f'l10n_ro_edi_stock_{location}_bcp']:
                errors.append(_("The border crossing point is missing under %(location_group)s", location_group=loc_group))
            elif loc_value == 'customs' and not data[f'l10n_ro_edi_stock_{location}_customs_office']:
                errors.append(_("The customs office is missing under %(location_group)s", location_group=loc_group))
            elif loc_value == 'location':
                match data['picking_type_id'].code:
                    case 'outgoing':
                        partner = data['picking_type_id'].warehouse_id.partner_id if location == 'start' else data['partner_id']
                    case 'incoming':
                        partner = data['picking_type_id'].warehouse_id.partner_id if location == 'end' else data['partner_id']
                    case _other:
                        errors.append(_("Invalid picking type %(type_code)s", type_code=_other))
                        continue

                missing_field_names = []
                if not partner.state_id:
                    missing_field_names.append(_("State"))
                if not partner.city:
                    missing_field_names.append(_("City"))
                if not partner.street:
                    missing_field_names.append(_("Street"))
                if not partner.zip:
                    missing_field_names.append(_("Postal Code"))

                if len(missing_field_names) == 1:
                    errors.append(_("%(location_group)s is missing the %(field_name)s field.", location_group=loc_group, field_name=missing_field_names[0]))
                elif len(missing_field_names) > 1:
                    errors.append(_("%(location_group)s is missing following fields: %(field_names)s", location_group=loc_group, field_names=missing_field_names))

        return errors