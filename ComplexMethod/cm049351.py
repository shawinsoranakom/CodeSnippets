def _get_combination_info(
        self, combination=False, product_id=False, add_qty=1.0, uom_id=False, only_template=False,
    ):
        """Return info about a given combination.

        Note: this method does not take into account whether the combination is
        actually possible.

        :param combination: recordset of `product.template.attribute.value`

        :param int product_id: `product.product` id. If no `combination`
            is set, the method will try to load the variant `product_id` if
            it exists instead of finding a variant based on the combination.

            If there is no combination, that means we definitely want a
            variant and not something that will have no_variant set.

        :param float add_qty: the quantity for which to get the info,
            indeed some pricelist rules might depend on it.
        :param int|None uom_id: the uom for which to get the info, as an `uom.uom` id.

        :param only_template: boolean, if set to True, get the info for the
            template only: ignore combination and don't try to find variant

        :return: dict with product/combination info:

            - product_id: the variant id matching the combination (if it exists)

            - product_template_id: the current template id

            - display_name: the name of the combination

            - price: the computed price of the combination, take the catalog
                price if no pricelist is given

            - price_extra: the computed extra price of the combination

            - list_price: the catalog price of the combination, but this is
                not the "real" list_price, it has price_extra included (so
                it's actually more closely related to `lst_price`), and it
                is converted to the pricelist currency (if given)

            - has_discounted_price: True if the pricelist discount policy says
                the price does not include the discount and there is actually a
                discount applied (price < list_price), else False
        """
        self.ensure_one()

        combination = combination or self.env['product.template.attribute.value']
        website = request.website.with_context(self.env.context)
        uom = self.env['uom.uom'].browse(uom_id) or self.uom_id

        if not product_id and not combination and not only_template:
            combination = self._get_first_possible_combination()

        if only_template:
            product = self.env['product.product']
        elif product_id:
            product = self.env['product.product'].browse(product_id)
            if (combination - product.product_template_attribute_value_ids):
                # If the combination is not fully represented in the given product
                #   make sure to fetch the right product for the given combination
                product = self._get_variant_for_combination(combination)
        else:
            product = self._get_variant_for_combination(combination)

        product_or_template = product or self
        combination = combination or product.product_template_attribute_value_ids

        display_name = product_or_template.with_context(display_default_code=False).display_name
        if not product:
            combination_name = combination._get_combination_name()
            if combination_name:
                display_name = f"{display_name} ({combination_name})"

        price_context = product_or_template._get_product_price_context(combination)
        product_or_template = product_or_template.with_context(**price_context)

        combination_info = {
            'combination': combination,
            'product_id': product.id,
            'product_template_id': self.id,
            'display_name': display_name,
            'is_combination_possible': self._is_combination_possible(combination=combination),

            **self._get_additionnal_combination_info(
                product_or_template=product_or_template,
                quantity=add_qty or 1.0,
                uom=uom,
                date=fields.Date.context_today(self),
                website=website,
            )
        }

        if website.google_analytics_key:
            combination_info['product_tracking_info'] = self._get_google_analytics_data(
                product,
                combination_info,
            )

        if (
            product_or_template.type == 'combo'
            and website.show_line_subtotals_tax_selection == 'tax_included'
            and not all(
                tax.price_include
                for tax
                in product_or_template.sudo().combo_ids.combo_item_ids.product_id.taxes_id
            )
        ):
            combination_info['tax_disclaimer'] = _(
                "Final price may vary based on selection. Tax will be calculated at checkout."
            )

        return combination_info