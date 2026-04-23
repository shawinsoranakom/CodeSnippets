def _get_sale_order_line_multiline_description_variants(self):
        """When using no_variant attributes or is_custom values, the product
        itself is not sufficient to create the description: we need to add
        information about those special attributes and values.

        :return: the description related to special variant attributes/values
        :rtype: string
        """
        no_variant_ptavs = self.product_no_variant_attribute_value_ids._origin.filtered(
            # Only describe the attributes where a choice was made by the customer
            lambda ptav: ptav.display_type == 'multi' or ptav.attribute_line_id.value_count > 1
        )
        if not self.product_custom_attribute_value_ids and not no_variant_ptavs:
            return ""

        name = ""

        custom_ptavs = self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id
        multi_ptavs = no_variant_ptavs.filtered(lambda ptav: ptav.display_type == 'multi').sorted()

        # display the no_variant attributes, except those that are also
        # displayed by a custom (avoid duplicate description)
        for ptav in (no_variant_ptavs - multi_ptavs - custom_ptavs):
            name += "\n" + ptav.display_name

        # display the selected values per attribute on a single for a multi checkbox
        for pta, ptavs in groupby(multi_ptavs, lambda ptav: ptav.attribute_id):
            name += "\n" + _(
                "%(attribute)s: %(values)s",
                attribute=pta.name,
                values=", ".join(ptav.name for ptav in ptavs)
            )

        # Sort the values according to _order settings, because it doesn't work for virtual records in onchange
        sorted_custom_ptav = self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id.sorted()
        for patv in sorted_custom_ptav:
            pacv = self.product_custom_attribute_value_ids.filtered(lambda pcav: pcav.custom_product_template_attribute_value_id == patv)
            name += "\n" + pacv.display_name

        return name