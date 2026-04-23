def _skip_for_no_variant(self, product, bom_attribule_values, never_attribute_values=False):
        """ Controls if a Component/Operation/Byproduct line should be skipped based on the 'no_variant' attributes
            Cases:
                - no_variant:
                    1. attribute present on the line
                        => need to be at least one attribute value matching between the one passed as args and the ones one the line
                    2. attribute not present on the line
                        => valid if the line has no attribute value selected for that attribute
                - always and dynamic: match_all_variant_values()
        """
        no_variant_bom_attributes = bom_attribule_values.filtered(lambda av: av.attribute_id.create_variant == 'no_variant')

        # Attributes create_variant 'always' and 'dynamic'
        other_attribute_valid = product._match_all_variant_values(bom_attribule_values - no_variant_bom_attributes)

        # If there are no never attribute values on the line => 'always' and 'dynamic'
        if not no_variant_bom_attributes:
            return not other_attribute_valid

        # Or if there are never attribute on the line values but no value is passed => impossible to match
        if not never_attribute_values:
            return True

        bom_values_by_attribute = no_variant_bom_attributes.grouped('attribute_id')
        never_values_by_attribute = never_attribute_values.grouped('attribute_id')

        # Or if there is no overlap between given line values attributes and the ones on on the bom
        if not any(never_att_id in no_variant_bom_attributes.attribute_id.ids for never_att_id in never_attribute_values.attribute_id.ids):
            return True

        # Check that at least one variant attribute is correct
        for attribute, values in bom_values_by_attribute.items():
            if never_values_by_attribute.get(attribute) and any(val.id in never_values_by_attribute[attribute].ids for val in values):
                return not other_attribute_valid

        # None were found, so we skip the line
        return True