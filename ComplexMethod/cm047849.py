def _get_aggregated_product_quantities(self, **kwargs):
        """Returns dictionary of products and corresponding values of interest grouped by optional kit_name

        Removes descriptions where description == kit_name. kit_name is expected to be passed as a
        kwargs value because this is not directly stored in move_line_ids. Unfortunately because we
        are working with aggregated data, we have to loop through the aggregation to do this removal.

        arguments: kit_name (optional): string value of a kit name passed as a kwarg
        returns: dictionary {same_key_as_super: {same_values_as_super, ...}
        """
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        kit_name = kwargs.get('kit_name')

        to_be_removed = []
        for aggregated_move_line in aggregated_move_lines:
            bom = aggregated_move_lines[aggregated_move_line]['bom']
            is_phantom = bom.type == 'phantom' if bom else False
            if kit_name:
                product = bom.product_id or bom.product_tmpl_id if bom else False
                display_name = product.display_name if product else False
                description = aggregated_move_lines[aggregated_move_line]['description']
                if not is_phantom or display_name != kit_name:
                    to_be_removed.append(aggregated_move_line)
                elif description == kit_name:
                    aggregated_move_lines[aggregated_move_line]['description'] = ""
            elif not kwargs and is_phantom:
                to_be_removed.append(aggregated_move_line)

        for move_line in to_be_removed:
            del aggregated_move_lines[move_line]

        return aggregated_move_lines