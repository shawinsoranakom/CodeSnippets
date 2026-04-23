def pricelist_change(self, pricelist, **post):
        website = request.env['website'].get_current_website()
        redirect_url = request.httprequest.referrer
        prev_pricelist = request.pricelist
        if (
            self._apply_selectable_pricelist(pricelist.id)
            and redirect_url
            and website.is_view_active('website_sale.filter_products_price')
            and prev_pricelist != pricelist
        ):
            # Convert prices to the new priceslist currency in the query params of the referrer
            decoded_url = url_parse(redirect_url)
            args = url_decode(decoded_url.query)
            min_price = args.get('min_price')
            max_price = args.get('max_price')
            if min_price or max_price:
                try:
                    min_price = float(min_price)
                    args['min_price'] = min_price and str(prev_pricelist.currency_id._convert(
                        min_price,
                        pricelist.currency_id,
                        request.website.company_id,
                        fields.Date.today(),
                        round=False,
                    ))
                except (ValueError, TypeError):
                    pass
                try:
                    max_price = float(max_price)
                    args['max_price'] = max_price and str(prev_pricelist.currency_id._convert(
                        max_price,
                        pricelist.currency_id,
                        request.website.company_id,
                        fields.Date.today(),
                        round=False,
                    ))
                except (ValueError, TypeError):
                    pass
            redirect_url = decoded_url.replace(query=url_encode(args)).to_url()

        return request.redirect(redirect_url or self._get_shop_path())