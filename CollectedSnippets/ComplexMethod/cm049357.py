def _get_pl_partner_order(
        self, country_code, show_visible, current_pl_id, website_pricelist_ids, partner_pl_id=False
    ):
        """ Return the list of pricelists that can be used on website for the current user.

        :param str country_code: code iso or False, If set, we search only price list available for this country
        :param bool show_visible: if True, we don't display pricelist where selectable is False (Eg: Code promo)
        :param int current_pl_id: The current pricelist used on the website
            (If not selectable but currently used anyway, e.g. pricelist with promo code)
        :param tuple website_pricelist_ids: List of ids of pricelists available for this website
        :param int partner_pl_id: the partner pricelist
        :returns: list of product.pricelist ids
        :rtype: list
        """
        self.ensure_one()
        pricelists = self.env['product.pricelist']

        def check_pricelist(pricelist):
            if show_visible:
                return pricelist.selectable or pricelist.id == current_pl_id
            else:
                return True

        # Note: 1. pricelists from all_pl are already website compliant (went through
        #          `_get_website_pricelists_domain`)
        #       2. do not read `property_product_pricelist` here as `_get_pl_partner_order`
        #          is cached and the result of this method will be impacted by that field value.
        #          Pass it through `partner_pl_id` parameter instead to invalidate the cache.

        # If there is a GeoIP country, find a pricelist for it
        if country_code:
            pricelists |= self.env['res.country.group'].search(
                [('country_ids.code', '=', country_code)]
            ).pricelist_ids.filtered(
                lambda pl: pl._is_available_on_website(self) and check_pricelist(pl)
            )

        # no GeoIP or no pricelist for this country
        if not pricelists:
            pricelists = pricelists.browse(website_pricelist_ids).filtered(
                lambda pl: check_pricelist(pl) and not (country_code and pl.country_group_ids))

        # if logged in, add partner pl (which is `property_product_pricelist`, might not be website compliant)
        if not self.env.user._is_public():
            # keep partner_pricelist only if website compliant
            partner_pricelist = pricelists.browse(partner_pl_id).filtered(
                lambda pl:
                    pl._is_available_on_website(self)
                    and check_pricelist(pl)
                    and pl._is_available_in_country(country_code)
            )
            pricelists |= partner_pricelist

        # This method is cached, must not return records! See also #8795
        # sudo is needed to ensure no records rules are applied during the sorted call,
        # we only want to reorder the records on hand, not filter them.
        return pricelists.sudo().sorted().ids