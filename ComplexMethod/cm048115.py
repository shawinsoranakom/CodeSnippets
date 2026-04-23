def _export_invoice_constraints(self, invoice, vals):
        # EXTENDS account_edi_ubl_cii
        constraints = super()._export_invoice_constraints(invoice, vals)

        # Tax category must be filled on the line, with a value from SG categories.
        tax_total_node = vals['document_node']['cac:TaxTotal'][0]
        for tax_subtotal_node in tax_total_node['cac:TaxSubtotal']:
            if any(tax_category_node['cbc:ID']['_text'] not in ANZ_TAX_CATEGORIES for tax_category_node in tax_subtotal_node['cac:TaxCategory']):
                constraints['anz_vat_category_required'] = _("You must set a tax category on each taxes of the invoice.\nValid categories are: S, E, Z, G, O")

        # Tax category of type "Not subject to tax" must have tax amount 0
        count_outside_of_scope_breakdown = 0
        for tax_subtotal in tax_total_node['cac:TaxSubtotal']:
            if any(tax_category_node['cbc:ID']['_text'] != 'O' for tax_category_node in tax_subtotal['cac:TaxCategory']):
                continue
            count_outside_of_scope_breakdown += 1

            if float_is_zero(tax_subtotal['cbc:TaxAmount']['_text'], precision_digits=2):
                continue

            if vals['supplier'].ref_company_ids[:1].l10n_au_is_gst_registered:
                constraints['anz_tax_breakdown_amount'] = \
                    self.env._("A tax category of type 'Not subject to tax' must have tax"
                               " amount set to 0")
            else:
                # If a company is not GST registered, this module remaps all tax categories
                # to 'O' (Other/Out of Scope). This causes an issue when a line contained a
                # non-zero tax, as it would create a tax subtotal with (Code: 'O', Amount:
                # non-zero), which violates PINT rules.
                # Since the code silently remaps tax classification code, the original error
                # message might be misleading for users. This constraint contains better
                # explaination of error and intructions on how to prevent it.
                constraints['anz_non_gst_supplier_tax_scope'] = \
                    self.env._("Suppliers not registered for GST cannot use taxes that are"
                               " not zero-rated. Please ensure the tax category is set to"
                               " 'O' (Services outside scope of tax) with a tax amount of 0.")

        # There should be at most one tax breakdown of type "Not subject to tax".
        if count_outside_of_scope_breakdown > 1 and vals['supplier'].ref_company_ids[:1].l10n_au_is_gst_registered:
            constraints['anz_duplicate_tax_breakdown'] = \
                self.env._("A tax breakdown of type 'Not subject to tax' should appear at most"
                           " once in the tax breakdown")

        # ALIGNED-IBR-001-AUNZ and ALIGNED-IBR-002-AUNZ
        for partner_type in ('supplier', 'customer'):
            partner = vals[partner_type]
            if partner.country_code == 'AU' and partner.peppol_eas != '0151':
                constraints[f'au_{partner_type}_eas_0151'] = _("The Peppol EAS must be set to ABN (0151) if the partner country is Australia.")
            elif partner.country_code == 'NZ' and partner.peppol_eas != '0088':
                constraints[f'nz_{partner_type}_eas_0088'] = _("The Peppol EAS must be set to EAN (0088) if the partner country is New Zealand.")

        return constraints