def _get_product_information(
        self,
        product_template,
        combination,
        currency,
        pricelist,
        so_date,
        quantity=1,
        product_uom_id=None,
        parent_combination=None,
        show_packaging=True,
        **kwargs,
    ):
        """Return complete information about a product.

        :param product.template product_template: The product for which to seek information.
        :param product.template.attribute.value combination: The combination of the product.
        :param res.currency currency: The currency of the transaction.
        :param product.pricelist pricelist: The pricelist to use.
        :param datetime so_date: The date of the `sale.order`, to compute the price at the right
            rate.
        :param int quantity: The quantity of the product.
        :param int|None product_uom_id: The unit of measure of the product, as a `uom.uom` id.
        :param product.template.attribute.value|None parent_combination: The combination of the
            parent product.
        :param dict kwargs: Locally unused data passed to `_get_basic_product_information`.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'product_tmpl_id': int,
                'id': int,
                'description_sale': str|False,
                'display_name': str,
                'price': float,
                'quantity': int
                'attribute_line': [{
                    'id': int
                    'attribute': {
                        'id': int
                        'name': str
                        'display_type': str
                    },
                    'attribute_value': [{
                        'id': int,
                        'name': str,
                        'price_extra': float,
                        'html_color': str|False,
                        'image': str|False,
                        'is_custom': bool
                    }],
                    'selected_attribute_id': int,
                }],
                'exclusions': dict,
                'archived_combination': dict,
                'parent_exclusions': dict,
                'available_uoms': dict (optional),
            }
        """
        uom = (
            (product_uom_id and request.env['uom.uom'].browse(product_uom_id))
            or product_template.uom_id
        )
        product = product_template._get_variant_for_combination(combination)
        attribute_exclusions = product_template._get_attribute_exclusions(
            parent_combination=parent_combination,
            combination_ids=combination.ids,
        )
        product_or_template = product or product_template
        ptals = product_template.attribute_line_ids
        attrs_map = {
            attr_data['id']: attr_data
            for attr_data in ptals.attribute_id.read(['id', 'name', 'display_type'])
        }
        ptavs = ptals.product_template_value_ids.filtered(lambda p: p.ptav_active or combination and p.id in combination.ids)
        ptavs_map = dict(zip(ptavs.ids, ptavs.read(['name', 'html_color', 'image', 'is_custom'])))

        values = dict(
            product_tmpl_id=product_template.id,
            **self._get_basic_product_information(
                product_or_template,
                pricelist,
                combination,
                quantity=quantity,
                uom=uom,
                currency=currency,
                date=so_date,
                **kwargs,
            ),
            quantity=quantity,
            uom=uom.read(['id', 'display_name'])[0],
            attribute_lines=[{
                'id': ptal.id,
                'attribute': dict(**attrs_map[ptal.attribute_id.id]),
                'attribute_values': [
                    dict(
                        **ptavs_map[ptav.id],
                        price_extra=self._get_ptav_price_extra(
                            ptav, currency, so_date, product_or_template
                        ),
                    ) for ptav in ptal.product_template_value_ids
                    if ptav.ptav_active or (combination and ptav.id in combination.ids)
                ],
                'selected_attribute_value_ids': combination.filtered(
                    lambda c: ptal in c.attribute_line_id
                ).ids,
                'create_variant': ptal.attribute_id.create_variant,
            } for ptal in product_template.attribute_line_ids],
            exclusions=attribute_exclusions['exclusions'],
            archived_combinations=attribute_exclusions['archived_combinations'],
            parent_exclusions=attribute_exclusions['parent_exclusions'],
        )
        if show_packaging and product_template._has_multiple_uoms():
            values['available_uoms'] = product_template._get_available_uoms().read(
                ['id', 'display_name']
            )
        # Shouldn't be sent client-side
        values.pop('pricelist_rule_id', None)
        return values