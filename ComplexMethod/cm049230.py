def _filter_combinations_impossible_by_config(self, combination_tuples, ignore_no_variant=False):
        """ Filter combination_tuples according to the config of attributes on the template

        :return: iterator over possible combinations
        :rtype: generator
        """
        self.ensure_one()
        attribute_lines = self.valid_product_template_attribute_line_ids
        attribute_lines_active_values = attribute_lines.product_template_value_ids._only_active()
        if ignore_no_variant:
            attribute_lines = attribute_lines._without_no_variant_attributes()
        attribute_lines_without_multi = attribute_lines.filtered(
            lambda l: l.attribute_id.display_type != 'multi')
        exclusions = self._get_own_attribute_exclusions()
        for combination_tuple in combination_tuples:
            combination = self.env['product.template.attribute.value'].concat(*combination_tuple)
            combination_without_multi = combination.filtered(
                lambda l: l.attribute_line_id.attribute_id.display_type != 'multi')
            if len(combination_without_multi) != len(attribute_lines_without_multi):
                # number of attribute values passed is different than the
                # configuration of attributes on the template
                continue
            if attribute_lines_without_multi != combination_without_multi.attribute_line_id:
                # combination has different attributes than the ones configured on the template
                continue
            if not (attribute_lines_active_values >= combination):
                # combination has different values than the ones configured on the template
                continue
            if exclusions:
                # exclude if the current value is in an exclusion,
                # and the value excluding it is also in the combination
                combination_ids = set(combination.ids)
                combination_excluded_ids = set(itertools.chain(*[exclusions.get(ptav_id) for ptav_id in combination.ids]))
                if combination_ids & combination_excluded_ids:
                    continue
            yield combination