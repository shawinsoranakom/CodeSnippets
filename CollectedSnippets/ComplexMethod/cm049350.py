def _get_sales_prices(self, website):
        if not self:
            return {}

        pricelist = request.pricelist
        currency = website.currency_id
        fiscal_position_sudo = request.fiscal_position
        date = fields.Date.context_today(self)

        pricelist_prices = pricelist._compute_price_rule(self, 1.0)
        comparison_prices_enabled = self.env['res.groups']._is_feature_enabled(
            'website_sale.group_product_price_comparison'
        )

        res = {}
        for template in self:
            pricelist_price, pricelist_rule_id = pricelist_prices[template.id]

            product_taxes = template.sudo().taxes_id._filter_taxes_by_company(self.env.company)
            taxes = fiscal_position_sudo.map_tax(product_taxes)

            base_price = None
            template_price_vals = {
                'price_reduce': self._apply_taxes_to_price(
                    pricelist_price, currency, product_taxes, taxes, template, website=website,
                ),
            }
            pricelist_item = template.env['product.pricelist.item'].browse(pricelist_rule_id)
            if pricelist_item._show_discount_on_shop():
                pricelist_base_price = pricelist_item._compute_price_before_discount(
                    product=template,
                    quantity=1.0,
                    date=date,
                    uom=template.uom_id,
                    currency=currency,
                )
                if currency.compare_amounts(pricelist_base_price, pricelist_price) == 1:
                    base_price = pricelist_base_price
                    template_price_vals['base_price'] = self._apply_taxes_to_price(
                        base_price, currency, product_taxes, taxes, template, website=website,
                    )

            if not base_price and comparison_prices_enabled and template.compare_list_price:
                template_price_vals['base_price'] = template.currency_id._convert(
                    template.compare_list_price,
                    currency,
                    self.env.company,
                    date,
                    round=False,
                )

            res[template.id] = template_price_vals

        return res