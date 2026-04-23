def create(self, vals_list):
        for values in vals_list:
            if values.get('product_id') and not values.get('product_tmpl_id'):
                # Deduce product template from product variant if not specified.
                # Ensures that the pricelist rule is properly configured and displayed in the UX
                # even in case of partial/incomplete data (mostly for imports).
                values['product_tmpl_id'] = self.env['product.product'].browse(
                    values.get('product_id')
                ).product_tmpl_id.id

            if not values.get('applied_on'):
                values['applied_on'] = (
                    '0_product_variant' if values.get('product_id') else
                    '1_product' if values.get('product_tmpl_id') else
                    '2_product_category' if values.get('categ_id') else
                    '3_global'
                )

            # Ensure item consistency for later searches.
            applied_on = values['applied_on']
            if applied_on == '3_global':
                values.update({'product_id': None, 'product_tmpl_id': None, 'categ_id': None})
            elif applied_on == '2_product_category':
                values.update({'product_id': None, 'product_tmpl_id': None})
            elif applied_on == '1_product':
                values.update({'product_id': None, 'categ_id': None})
            elif applied_on == '0_product_variant':
                values.update({'categ_id': None})
        return super().create(vals_list)