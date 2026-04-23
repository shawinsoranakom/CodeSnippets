def _get_and_cache_current_pricelist(self):
        """Retrieve and cache the current pricelist for the session.

        Note: self.ensure_one()

        :return: The determined pricelist, which could be empty, as a sudoed record.
        :rtype: product.pricelist
        """
        self.ensure_one()

        ProductPricelistSudo = self.env['product.pricelist'].sudo()
        if not self.env['res.groups']._is_feature_enabled('product.group_product_pricelist'):
            return ProductPricelistSudo  # Skip pricelist computation if pricelists are disabled.

        if PRICELIST_SESSION_CACHE_KEY in request.session:
            pricelist_sudo = ProductPricelistSudo.browse(
                request.session[PRICELIST_SESSION_CACHE_KEY]
            )
            if pricelist_sudo and (
                pricelist_sudo.exists()
                and pricelist_sudo._is_available_on_website(self)
                and pricelist_sudo._is_available_in_country(self._get_geoip_country_code())
            ):
                return pricelist_sudo.sudo()

        if cart_sudo := request.cart:
            if not request.env.cr.readonly:
                # If there is a cart, recompute on the cart and take it from there
                cart_sudo._compute_pricelist_id()
            pricelist_sudo = cart_sudo.pricelist_id
        else:
            pricelist_sudo = self.env.user.partner_id.property_product_pricelist
            available_pricelists = self.get_pricelist_available()
            if available_pricelists and pricelist_sudo not in available_pricelists:
                pricelist_sudo = available_pricelists[0].sudo()

        request.session[PRICELIST_SESSION_CACHE_KEY] = pricelist_sudo.id

        return pricelist_sudo