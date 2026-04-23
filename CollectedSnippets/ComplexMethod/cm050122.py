def _import_partners(self, tree):
        xpath_to_field = {
            './/cac:DespatchSupplierParty/cac:Party': 'partner_id',
            './/cac:CarrierParty': 'l10n_tr_nilvera_carrier_id',
            './/cac:BuyerCustomerParty/cac:Party': 'l10n_tr_nilvera_buyer_id',
            './/cac:SellerSupplierParty/cac:Party': 'l10n_tr_nilvera_seller_supplier_id',
            './/cac:OriginatorCustomerParty/cac:Party': 'l10n_tr_nilvera_buyer_originator_id',
        }

        partner_data = [
            (xpath, self._get_partner_vals_from_xml(tree, xpath))
            for xpath in xpath_to_field
        ]
        partner_data = {xpath: vals for xpath, vals in partner_data if vals}

        existing_partners = self.env['res.partner'].with_context(active_test=False).search_read(
            ['|', ('vat', 'in', [vals.get('vat') for vals in partner_data.values() if vals.get('vat')]),
             ('name', 'in', [vals.get('name') for vals in partner_data.values() if vals.get('name')])],
            ['id', 'vat', 'name'],
        )
        existing_dict = {partner['vat'] or partner['name']: partner['id'] for partner in existing_partners}

        partners_vals = {}
        for xpath, vals in partner_data.items():
            key = vals.get('vat') or vals.get('name')
            partners_vals[xpath_to_field[xpath]] = existing_dict.get(key) or self._create_partner_from_xml(vals)

        return partners_vals