def load(self, fields, data):
        """
        Data import for products depends on the presence of variants.
        If 'import_attribute_values' is present, then the product.template files
        will be created, followed by the product.product files. Everything is
        done from the same file.

        The required fields are always imported; however, other fields are
        imported when the product.product files are created.
        """
        if 'import_attribute_values' not in fields:
            return super().load(fields, data)

        column_no = fields.index('import_attribute_values')

        data_list_products = []
        data_list_templates = []
        for values in data:
            if values[column_no].strip():
                data_list_products.append(values)
            else:
                values = list(values)
                values.pop(column_no)
                data_list_templates.append(values)

        if data_list_templates:
            template_fields = list(fields)
            template_fields.pop(column_no)
            result = super().load(template_fields, data_list_templates)
            if any(message['type'] == 'error' for message in result['messages']):
                return result
        else:
            result = {'ids': [], 'messages': [], 'nextrow': 0}

        if data_list_products:
            ProductProduct = self.env['product.product'].with_context(from_template_import=True)
            result_product = ProductProduct.load(fields, data_list_products)
            if any(message['type'] == 'error' for message in result_product['messages']):
                return result_product

            product_templates = ProductProduct.browse(result_product['ids']).product_tmpl_id
            result['ids'].extend(product_templates.ids)
            result['messages'].extend(result_product['messages'])
            result['nextrow'] = result.get('nextrow', 0) + result_product.get('nextrow', 0)

        return result