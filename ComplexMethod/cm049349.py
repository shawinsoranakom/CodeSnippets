def _get_previewed_attribute_values(self, category=None, product_query_params=None):
        """Compute previewed product attribute values for each product in the recordset.

        :return: the previewed attribute values per product
        :rtype: dict
        """
        res = defaultdict(dict)
        show_count = 20
        for template in self:
            previewed_ptal = next((
                p for p in template.attribute_line_ids
                if p.attribute_id.preview_variants != 'hidden'
            ), None)
            if previewed_ptal:
                previewed_ptavs = [
                    ptav
                    for ptav in previewed_ptal.product_template_value_ids
                    if ptav.ptav_active and ptav.ptav_product_variant_ids
                ]

                if len(previewed_ptavs) > 1:
                    previewed_ptavs_data = []
                    for ptav in previewed_ptavs[:show_count]:
                        matching_variant = min(ptav.ptav_product_variant_ids, key=lambda p: p.id)
                        variant_query_params = {
                            **(product_query_params or {}),
                            'attribute_values': str(ptav.product_attribute_value_id.id)
                        }
                        previewed_ptavs_data.append({
                            'ptav': ptav,
                            'variant_image_url': self.env['website'].image_url(matching_variant, 'image_512'),
                            'variant_url': template._get_product_url(category, variant_query_params),
                        })

                    res[template.id] = {
                        'ptavs_data': previewed_ptavs_data,
                        'hidden_ptavs_count': max(0, len(previewed_ptavs) - show_count)
                    }
        return res