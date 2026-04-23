def _compute_l10n_ec_vat_validation(self):
        it_ruc = self.env.ref("l10n_ec.ec_ruc", False)
        it_dni = self.env.ref("l10n_ec.ec_dni", False)
        ruc = stdnum.util.get_cc_module("ec", "ruc")
        ci = stdnum.util.get_cc_module("ec", "ci")
        for partner in self:
            partner.l10n_ec_vat_validation = False
            if partner and partner.l10n_latam_identification_type_id in (it_ruc, it_dni) and partner.vat:
                final_consumer = verify_final_consumer(partner.vat)
                if not final_consumer:
                    if partner.l10n_latam_identification_type_id.id == it_dni.id and not ci.is_valid(partner.vat):
                        partner.l10n_ec_vat_validation = _("The VAT %s seems to be invalid as the tenth digit doesn't comply with the validation algorithm "
                                                           "(could be an old VAT number)", partner.vat)
                    if partner.l10n_latam_identification_type_id.id == it_ruc.id and not ruc.is_valid(partner.vat):
                        partner.l10n_ec_vat_validation = _("The VAT %s seems to be invalid as the tenth digit doesn't comply with the validation algorithm "
                                                           "(SRI has stated that this validation is not required anymore for some VAT numbers)", partner.vat)