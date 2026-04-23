def _import_ubl_invoice_line_add_product_values(self, collected_values):
        line_tree = collected_values['line_tree']
        partner = collected_values.get('customer_values', {}).get('customer')
        name = collected_values['to_write'].get('name')

        product_values = collected_values['product_values'] = {
            'default_code': line_tree.findtext('.//{*}Item/{*}SellersItemIdentification/{*}ID'),
            'name': line_tree.findtext('.//{*}Item/{*}Name'),
            'barcode': line_tree.findtext('.//{*}Item/{*}StandardItemIdentification/{*}ID[@schemeID="0160"]'),
            'invoice_predictive': {
                'invoice': collected_values['invoice'],
                'name': name,
                'partner': partner or self.env['res.partner'],
            },
        }

        # CommodityClassification
        for commodity_tree in line_tree.findall('./{*}Item/{*}CommodityClassification/{*}ItemClassificationCode'):
            list_id = commodity_tree.attrib.get('listID')
            code = commodity_tree.text
            if not list_id or not code:
                continue

            if list_id == 'HS':
                product_values['intrastat_code'] = code
            elif list_id == 'TST':
                product_values['unspsc_code'] = code
            elif list_id == 'STI':
                product_values['l10n_ro_cpv_code'] = code
            elif list_id == 'CG':
                product_values['cg_item_classification_code'] = code