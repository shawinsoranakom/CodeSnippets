def _create_attributes_from_gelato_info(self, template_info):
        """ Create attributes for the current product template.

        :param dict template_info: The template information fetched from Gelato.
        :return: None
        """
        if len(template_info['variants']) == 1:  # The template has no attribute.
            self.gelato_product_uid = template_info['variants'][0]['productUid']
        else:  # The template has multiple attributes.
            # Iterate over the variants to find and create the possible attributes.
            for variant_data in template_info['variants']:
                current_variant_pavs = self.env['product.attribute.value']
                for attribute_data in variant_data['variantOptions']:  # Attribute name and value.
                    # Search for the existing attribute with the proper variant creation policy and
                    # create it if not found.
                    attribute = self.env['product.attribute'].search(
                        [('name', '=', attribute_data['name']), ('create_variant', '=', 'always')],
                        limit=1,
                    )
                    if not attribute:
                        attribute = self.env['product.attribute'].create({
                            'name': attribute_data['name']
                        })

                    # Search for the existing attribute value and create it if not found.
                    attribute_value = self.env['product.attribute.value'].search([
                        ('name', '=', attribute_data['value']),
                        ('attribute_id', '=', attribute.id),
                    ], limit=1)
                    if not attribute_value:
                        attribute_value = self.env['product.attribute.value'].create({
                            'name': attribute_data['value'],
                            'attribute_id': attribute.id
                        })
                    current_variant_pavs += attribute_value

                    # Search for the existing PTAL and create it if not found.
                    ptal = self.env['product.template.attribute.line'].search(
                        [('product_tmpl_id', '=', self.id), ('attribute_id', '=', attribute.id)],
                        limit=1,
                    )
                    if not ptal:
                        self.env['product.template.attribute.line'].create({
                            'product_tmpl_id': self.id,
                            'attribute_id': attribute.id,
                            'value_ids': [Command.link(attribute_value.id)]
                        })
                    else:  # The PTAL already exists.
                        ptal.value_ids = [Command.link(attribute_value.id)]  # Link the value.

                # Find the variant that was automatically created and set the Gelato UID.
                for variant in self.product_variant_ids:
                    corresponding_ptavs = variant.product_template_attribute_value_ids
                    corresponding_pavs = corresponding_ptavs.product_attribute_value_id
                    if corresponding_pavs == current_variant_pavs:
                        variant.gelato_product_uid = variant_data['productUid']
                        break

            # Delete the incompatible variants that were created but not allowed by Gelato.
            variants_without_gelato = self.env['product.product'].search([
                ('product_tmpl_id', '=', self.id),
                ('gelato_product_uid', '=', False)
            ])
            variants_without_gelato.unlink()