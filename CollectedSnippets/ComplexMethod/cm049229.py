def _get_attribute_exclusions(
        self, parent_combination=None, parent_name=None, combination_ids=None
    ):
        """Return the list of attribute exclusions of a product.

        :param parent_combination: the combination from which
            `self` is an optional or accessory product. Indeed exclusions
            rules on one product can concern another product.
        :type parent_combination: recordset `product.template.attribute.value`
        :param parent_name: the name of the parent product combination.
        :type parent_name: str
        :param list combination_ids: The combination of the product, as a
            list of `product.template.attribute.value` ids.

        :return: dict of exclusions
            - exclusions: from this product itself
            - archived_combinations: list of archived combinations
            - parent_combination: ids of the given parent_combination
            - parent_exclusions: from the parent_combination
           - parent_product_name: the name of the parent product if any, used in the interface
               to explain why some combinations are not available.
               (e.g: Not available with Customizable Desk (Legs: Steel))
           - mapped_attribute_names: the name of every attribute values based on their id,
               used to explain in the interface why that combination is not available
               (e.g: Not available with Color: Black)
        """
        self.ensure_one()
        parent_combination = parent_combination or self.env['product.template.attribute.value']
        archived_products = self.with_context(active_test=False).product_variant_ids.filtered(lambda l: not l.active)
        active_combinations = set(tuple(product.product_template_attribute_value_ids.ids) for product in self.product_variant_ids)
        return {
            'exclusions': self._complete_inverse_exclusions(
                self._get_own_attribute_exclusions(combination_ids=combination_ids)
            ),
            'archived_combinations': list(set(
                tuple(product.product_template_attribute_value_ids.ids)
                for product in archived_products
                if product.product_template_attribute_value_ids and all(
                    ptav.ptav_active or combination_ids and ptav.id in combination_ids
                    for ptav in product.product_template_attribute_value_ids
                )
            ) - active_combinations),
            'parent_exclusions': self._get_parent_attribute_exclusions(parent_combination),
            'parent_combination': parent_combination.ids,
            'parent_product_name': parent_name,
            'mapped_attribute_names': self._get_mapped_attribute_names(parent_combination),
        }