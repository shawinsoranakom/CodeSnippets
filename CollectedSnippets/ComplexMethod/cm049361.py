def _prepare_gmc_price_info(self, product):
        """Prepare price-related information for Google Merchant Center.

        Note: If the product is flagged to prevent zero price sales, an empty dictionary is
        returned.

        :return: A dictionary containing nothing if the product is "prevent zero price sale", or:
            - List price,
            - Sale price (if applicable), and
            - Comparison prices (e.g., $100 / ml) if "Product Reference Price" is enabled.
        :rtype: dict
        """
        price_context = product._get_product_price_context(
            product.product_template_attribute_value_ids
        )
        combination_info = product.with_context(
            **price_context,
        ).product_tmpl_id._get_additionnal_combination_info(
            product,
            quantity=1.0,
            uom=product.uom_id,
            date=fields.Date.context_today(self),
            website=self.website_id,
        )
        if combination_info['prevent_zero_price_sale']:
            return {}

        price_info = {
            'price': utils.gmc_format_price(
                combination_info['list_price'], combination_info['currency'],
            ),
        }

        if combination_info['has_discounted_price']:
            price_info['sale_price'] = utils.gmc_format_price(
                combination_info['price'], combination_info['currency'],
            )
            start_date = combination_info['discount_start_date']
            end_date = combination_info['discount_end_date']
            if start_date and end_date:
                price_info['sale_price_effective_date'] = '/'.join(
                    map(utils.gmc_format_date, (start_date, end_date)),
                )

        # Note: Google only supports a restricted set of unit and computes the comparison prices
        # differently than Odoo.
        # Ex: product="Pack of wine (6 bottles)", price=$65.00, uom_name="Pack".
        #   - in odoo: base_unit_count=6.0, base_unit_name="750ml"
        #       => displayed: "$10.83 / 750ml"
        #   - in google: unit_pricing_measure="4500ml", unit_pricing_base_measure="750ml"
        #       => displayed: "$10.83 / 750ml"
        if (
            combination_info.get('base_unit_name')
            and product.base_unit_count
            and (match := const.GMC_BASE_MEASURE.match(
                combination_info['base_unit_name'].strip().lower()
            ))
        ):
            base_count, base_unit = match['base_count'] or '1', match['base_unit']
            count = product.base_unit_count * int(base_count)
            if (
                base_unit in const.GMC_SUPPORTED_UOM
                and not float_is_zero(count, precision_digits=2)
            ):
                price_info['unit_pricing_measure'] = (
                    f'{float_round(count, precision_digits=2)}{base_unit}'
                )
                price_info['unit_pricing_base_measure'] = f'{base_count}{base_unit}'

        return price_info