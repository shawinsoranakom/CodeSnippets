def _cart_accessories(self):
        """ Suggest accessories based on 'Accessory Products' of products in cart """
        product_ids = set(self.website_order_line.product_id.ids)
        all_accessory_products = self.env['product.product']
        for line in self.website_order_line.filtered('product_id'):
            accessory_products = line.product_id.product_tmpl_id._get_website_accessory_product()
            if accessory_products:
                # Do not read ptavs if there is no accessory products to filter
                combination = line.product_id.product_template_attribute_value_ids + line.product_no_variant_attribute_value_ids
                all_accessory_products |= accessory_products.filtered(lambda product:
                    product.id not in product_ids
                    and product._website_show_quick_add()
                    and product.filtered_domain(self.env['product.product']._check_company_domain(line.company_id))
                    and product._is_variant_possible(parent_combination=combination)
                    and (
                        not self.website_id.prevent_zero_price_sale
                        or product._get_contextual_price()
                    )
                )

        return random.sample(all_accessory_products, len(all_accessory_products))