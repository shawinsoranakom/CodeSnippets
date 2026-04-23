def _get_possible_combinations(self, parent_combination=None, necessary_values=None):
        """Generator returning combinations that are possible, following the
        sequence of attributes and values.

        See `_is_combination_possible` for what is a possible combination.

        When encountering an impossible combination, try to change the value
        of attributes by starting with the further regarding their sequences.

        Ignore attributes that have no values.

        :param parent_combination: combination from which `self` is an
            optional or accessory product.
        :type parent_combination: recordset `product.template.attribute.value`

        :param necessary_values: values that must be in the returned combination
        :type necessary_values: recordset of `product.template.attribute.value`

        :return: the possible combinations
        :rtype: generator of recordset of `product.template.attribute.value`
        """
        self.ensure_one()

        if not self.active:
            return _("The product template is archived so no combination is possible.")

        necessary_values = necessary_values or self.env['product.template.attribute.value']
        necessary_attribute_lines = necessary_values.mapped('attribute_line_id')
        attribute_lines = self.valid_product_template_attribute_line_ids.filtered(
            lambda ptal: ptal not in necessary_attribute_lines)

        if not attribute_lines and self._is_combination_possible(necessary_values, parent_combination):
            yield necessary_values

        product_template_attribute_values_per_line = []
        for ptal in attribute_lines:
            if ptal.attribute_id.display_type != 'multi':
                values_to_add = ptal.product_template_value_ids._only_active()
            else:
                values_to_add = self.env['product.template.attribute.value']
            product_template_attribute_values_per_line.append(values_to_add)

        for partial_combination in self._cartesian_product(product_template_attribute_values_per_line, parent_combination):
            combination = partial_combination + necessary_values
            if self._is_combination_possible(combination, parent_combination):
                yield combination

        return _("There are no remaining possible combination.")