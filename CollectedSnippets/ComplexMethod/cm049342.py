def _update_address(self, partner_id, fnames=None):
        if not fnames:
            return

        fpos_before = self.fiscal_position_id
        pricelist_before = self.pricelist_id

        self.write(dict.fromkeys(fnames, partner_id))

        fpos_changed = fpos_before != self.fiscal_position_id
        if fpos_changed:
            # Recompute taxes on fpos change
            self._recompute_taxes()

            new_fpos = self.fiscal_position_id
            request.session[FISCAL_POSITION_SESSION_CACHE_KEY] = new_fpos.id
            request.fiscal_position = new_fpos

        #If user explicitely selected a valid pricelist, we don't want to change it
        if selected_pricelist_id := request.session.get(PRICELIST_SELECTED_SESSION_CACHE_KEY):
            selected_pricelist = (
                self.env['product.pricelist'].browse(selected_pricelist_id).exists()
            )
            if (
                selected_pricelist
                and selected_pricelist._is_available_on_website(self.website_id)
                and selected_pricelist._is_available_in_country(
                    self.partner_id.country_id.code
                )
            ):
                self.pricelist_id = selected_pricelist
            else:
                request.session.pop(PRICELIST_SELECTED_SESSION_CACHE_KEY, None)

        if self.pricelist_id != pricelist_before or fpos_changed:
            # Pricelist may have been recomputed by the `partner_id` field update
            # we need to recompute the prices to match the new pricelist if it changed
            self._recompute_prices()

            new_pricelist = self.pricelist_id
            request.session[PRICELIST_SESSION_CACHE_KEY] = new_pricelist.id
            request.pricelist = new_pricelist

        if self.carrier_id and 'partner_shipping_id' in fnames and self._has_deliverable_products():
            # Update the delivery method on shipping address change.
            delivery_methods = self._get_delivery_methods()
            delivery_method = self._get_preferred_delivery_method(delivery_methods)
            self._set_delivery_method(delivery_method)