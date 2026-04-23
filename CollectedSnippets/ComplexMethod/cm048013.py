def _l10n_es_edi_verifactu_get_suggested_clave_regimen(self, special_regime, forced_tax_applicability=None):
        """
        Return a suggested Clave Regimen for the taxes in `self` to be used for the Veri*Factu document.
        Note: Currently we only support one Clave Regimen for a whole Veri*Factu document.
        """
        taxes = self
        if forced_tax_applicability:
            # Remove main taxes with a different Veri*Factu tax applicability
            main_tax_types = self._l10n_es_get_main_tax_types()
            taxes = taxes.filtered(
                lambda tax: (tax.l10n_es_type not in main_tax_types
                             or tax._l10n_es_edi_verifactu_get_applicability() == forced_tax_applicability)
            )

        tax_applicability = forced_tax_applicability or taxes._l10n_es_edi_verifactu_get_applicability()
        if not tax_applicability:
            return False

        VAT = tax_applicability == '01'
        IGIC = tax_applicability == '03'
        if not (VAT or IGIC):
            return False

        recargo_taxes = taxes.filtered(lambda tax: tax.l10n_es_type == 'recargo')
        oss_tag = self.env.ref('l10n_eu_oss.tag_oss', raise_if_not_found=False)

        regimen_key = None
        if VAT and oss_tag and oss_tag.id in taxes.repartition_line_ids.tag_ids.ids:
            # oss
            regimen_key = '17_iva'
        elif taxes.filtered(lambda tax: tax.l10n_es_type == 'exento' and tax.l10n_es_exempt_reason == 'E2'):
            # export
            regimen_key = '02'
        elif VAT and special_regime == 'simplified':
            # simplified
            regimen_key = '20_iva'
        elif VAT and special_regime == 'reagyp':
            # REAGYP
            regimen_key = '19_iva'
        elif VAT and (recargo_taxes or special_regime == 'recargo'):
            # recargo
            regimen_key = '18_iva'
        else:
            regimen_key = '01'

        return regimen_key