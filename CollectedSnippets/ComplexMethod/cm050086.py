def _ubl_add_line_item_name_description_nodes(self, vals):
        item_node = vals['item_node']
        base_line = vals['line_vals']['base_line']
        product = base_line['product_id']

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