def _l10n_tr_validate_edispatch_on_done(self):
        partners = (
            self.company_id.partner_id
            | self.partner_id
            | self.partner_id.commercial_partner_id
            | self.l10n_tr_nilvera_carrier_id
            | self.l10n_tr_nilvera_buyer_id
            | self.l10n_tr_nilvera_seller_supplier_id
            | self.l10n_tr_nilvera_buyer_originator_id
        )

        error_messages = partners._l10n_tr_nilvera_validate_partner_details()

        if self.l10n_tr_nilvera_dispatch_type == 'MATBUDAN':
            if not self.l10n_tr_nilvera_delivery_date:
                error_messages['invalid_matbudan_date'] = {
                    'message': _("Printed Delivery Note Date is required."),
                }
            if (
                not self.l10n_tr_nilvera_delivery_printed_number
                or len(self.l10n_tr_nilvera_delivery_printed_number) != 16
            ):
                error_messages['invalid_matbudan_number'] = {
                    'message': _("Printed Delivery Note Number of 16 characters is required."),
                }

        invalid_country_drivers = self.l10n_tr_nilvera_driver_ids.filtered(
            lambda driver: not driver.country_id or driver.country_id.code != 'TR'
        )
        invalid_tckn_drivers = (self.l10n_tr_nilvera_driver_ids - invalid_country_drivers).filtered(
            lambda driver: not driver.vat or (driver.vat and len(driver.vat) != 11)
        )

        if drivers := len(invalid_country_drivers):
            error_messages['invalid_driver_country'] = {
                'message': _(
                    "Only Drivers from Türkiye are valid. Please update the Country and enter a valid TCKN in the Tax ID."
                ),
                'action_text': _(
                    "View %s",
                    (drivers == 1 and invalid_country_drivers.name) or _("Drivers"),
                ),
                'action': invalid_country_drivers._get_records_action(
                    name=_("Drivers"),
                ),
            }
        if drivers := len(invalid_tckn_drivers):
            driver_placeholder = drivers > 1 and _("Drivers") or _("%s's", invalid_tckn_drivers.name)
            error_messages['invalid_driver_tckn'] = {
                'message': _("%s TCKN is required.", driver_placeholder),
                'action_text': _("View %s", drivers == 1 and invalid_tckn_drivers.name or _("Drivers")),
                'action': invalid_tckn_drivers._get_records_action(name=_("Drivers")),
            }

        if (
            not self.l10n_tr_nilvera_carrier_id
            and not self.l10n_tr_nilvera_driver_ids
            and not self.l10n_tr_vehicle_plate
        ):
            error_messages['required_carrier_details'] = {
                'message': _("Carrier is required (optional when both the Driver and Vehicle Plate are filled)."),
            }

        elif not self.l10n_tr_nilvera_carrier_id and not self.l10n_tr_nilvera_driver_ids:
            error_messages['required_driver_details'] = {
                'message': _("At least one Driver is required."),
            }

        elif not self.l10n_tr_nilvera_carrier_id and not self.l10n_tr_vehicle_plate:
            error_messages['required_vehicle_details'] = {
                'message': _("Vehicle Plate is required."),
            }

        return error_messages or False