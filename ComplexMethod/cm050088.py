def _ubl_get_line_item_node(self, vals, item_values):
        # TO BE REMOVED IN MASTER
        _logger.warning("DEPRECATED")
        item_node = {}
        base_line = item_values['base_line']
        product = base_line['product_id']

        if product.default_code:
            item_node['cac:SellersItemIdentification'] = {
                'cbc:ID': {'_text': product.default_code},
            }
        else:
            item_node['cac:SellersItemIdentification'] = None
        if product.barcode:
            item_node['cac:StandardItemIdentification'] = {
                'cbc:ID': {
                    '_text': product.barcode,
                    'schemeID': '0160',  # GTIN
                },
            }
        else:
            item_node['cac:StandardItemIdentification'] = None
        item_node['cac:AdditionalItemProperty'] = [
            {
                'cbc:Name': {'_text': value.attribute_id.name},
                'cbc:Value': {'_text': value.name},
            }
            for value in product.product_template_attribute_value_ids
        ]

        if base_line.get('_removed_tax_data'):
            # Emptying tax extra line.
            name = description = base_line['_removed_tax_data']['tax'].name
        else:
            name = product.name or ''
            if line_name := base_line.get('name'):
                # Regular business line.
                description = line_name
                if not name:
                    name = line_name
            else:
                # Undefined line.
                description = product.description_sale or ''

        if description:
            item_node['cbc:Description'] = {'_text': description}
        else:
            item_node['cbc:Description'] = None

        if name:
            item_node['cbc:Name'] = {'_text': name}
        else:
            item_node['cbc:Name'] = None

        item_node['cac:ClassifiedTaxCategory'] = [
            self._ubl_get_line_item_node_classified_tax_category_node(vals, tax_category)
            for tax_category in item_values['classified_tax_categories'].values()
        ]
        return item_node