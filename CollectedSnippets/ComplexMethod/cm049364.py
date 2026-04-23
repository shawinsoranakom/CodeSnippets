def _filter_records_to_values(self, records, **options):
        hide_variants = self.env.context.get('hide_variants') and not isinstance(records, list)
        if hide_variants:
            product_limit = self.env.context.get('product_limit') or self.limit
            records = records.product_tmpl_id[:product_limit]
        res_products = super()._filter_records_to_values(records, **options)
        if (self.model_name or options.get('res_model')) == 'product.product':
            for res_product in res_products:
                product = res_product.get('_record')
                if not options.get('is_sample'):
                    if hide_variants and not product.has_configurable_attributes:
                        # Still display a product.product if the template is not configurable
                        res_product['_record'] = product = product.product_variant_id

                    # TODO VFE combination_info is only called to get the price here
                    # factorize and avoid computing the rest
                    if product.is_product_variant:
                        res_product.update(product._get_combination_info_variant())
                    elif hide_variants:
                        res_product.update(product._get_combination_info(only_template=True))
                        # Re-add product_id since it is set to false and required by some tests
                        res_product['product_id'] = product.product_variant_id.id
                    else:
                        res_product.update(product._get_combination_info())

                    if records.env.context.get('add2cart_rerender'):
                        res_product['_add2cart_rerender'] = True
                else:
                    res_product.update({
                        'is_sample': True,
                    })
        return res_products