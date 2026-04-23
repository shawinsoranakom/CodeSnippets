def _get_concept(self):
        """ Method to get the concept of the invoice considering the type of the products on the invoice """
        self.ensure_one()
        invoice_lines = self.invoice_line_ids.filtered(lambda x: x.display_type not in ('line_section', 'line_subsection', 'line_note'))
        product_types = set([x.product_id.type for x in invoice_lines if x.product_id])
        consumable = {'consu'}
        service = set(['service'])
        # on expo invoice you can mix services and products
        expo_invoice = self.l10n_latam_document_type_id.code in ['19', '20', '21']

        # WSFEX 1668 - If Expo invoice and we have a "IVA Liberado – Ley Nº 19.640" (Zona Franca) partner
        # then ARCA concept to use should be type "Others (4)"
        is_zona_franca = self.partner_id.l10n_ar_afip_responsibility_type_id == self.env.ref("l10n_ar.res_IVA_LIB")
        # Default value "product"
        afip_concept = '1'
        if expo_invoice and is_zona_franca:
            afip_concept = '4'
        elif product_types == service:
            afip_concept = '2'
        elif product_types - consumable and product_types - service and not expo_invoice:
            afip_concept = '3'
        return afip_concept