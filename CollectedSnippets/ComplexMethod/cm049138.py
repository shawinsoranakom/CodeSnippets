def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id or self.env.context.get('skip_uom_conversion') or (line.technical_price_unit != line.price_unit):
                continue
            params = line._get_select_sellers_params()

            if line.selected_seller_id or not line.date_planned:
                line.date_planned = line._get_date_planned(line.selected_seller_id).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # record product names to avoid resetting custom descriptions
            default_names = []
            display_names = []
            vendors = line.product_id._prepare_sellers(params=params)
            product_ctx = {'seller_id': None, 'partner_id': None, 'lang': get_lang(line.env, line.partner_id.lang).code}
            line_without_seller = line.product_id.with_context(product_ctx)
            default_names.append(line._get_product_purchase_description(line_without_seller))
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
                display_names.append(line.product_id.with_context(product_ctx).display_name)
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': line.selected_seller_id.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))
            else:
                # Checks that the product vendor and vendor name are correct
                for vendor, display_name in zip(vendors, display_names):
                    if line.name.startswith(display_name):
                        if not line.selected_seller_id:
                            line.name = line_without_seller.display_name + line.name[len(display_name):]
                        elif vendor.id != line.selected_seller_id.id:
                            line.name = display_names[vendors.ids.index(line.selected_seller_id.id)] + line.name[len(display_name):]
                        break

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not line.selected_seller_id:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom_id == line._origin.product_uom_id:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                line.discount = 0
                po_line_uom = line.product_uom_id or line.product_id.uom_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.tax_ids,
                    line.company_id,
                )
                price_unit = line.product_id.cost_currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order or fields.Date.context_today(line),
                    False
                )
                line.price_unit = line.technical_price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))

            elif line.selected_seller_id:
                price_unit = line.env['account.tax']._fix_tax_included_price_company(line.selected_seller_id.price, line.product_id.supplier_taxes_id, line.tax_ids, line.company_id) if line.selected_seller_id else 0.0
                price_unit = line.selected_seller_id.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)
                price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
                line.price_unit = line.technical_price_unit = line.selected_seller_id.product_uom_id._compute_price(price_unit, line.product_uom_id)
                line.discount = line.selected_seller_id.discount or 0.0