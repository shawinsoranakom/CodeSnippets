def _get_country_pricelist_multi(self, country_ids):
        def get_param_id(key):
            string_value = self.env['ir.config_parameter'].sudo().get_param(key, False)
            try:
                return int(string_value)
            except (TypeError, ValueError, OverflowError):
                return None

        company_id = self.env.company.id
        pl_domain = self._get_partner_pricelist_multi_search_domain_hook(company_id)

        if (
            (ctx_code := self.env.context.get('country_code'))
            and (ctx_country := self.env['res.country'].search([('code', '=', ctx_code)], limit=1))
        ):
            if ctx_country.id not in country_ids:
                country_ids.append(ctx_country.id)
        else:
            ctx_country = False

        # get fallback pricelist when no pricelist for a given country
        pl_fallback = (
            self.search(pl_domain + [('country_group_ids', '=', False)], limit=1)
            # save data in ir.config_parameter instead of ir.default for
            # res.partner.property_product_pricelist
            # otherwise the data will become the default value while
            # creating without specifying the property_product_pricelist
            # however if the property_product_pricelist is not specified
            # the result of the previous line should have high priority
            # when computing
            or self.browse(get_param_id(f'res.partner.property_product_pricelist_{company_id}'))
            or self.browse(get_param_id('res.partner.property_product_pricelist'))
            or self.search(pl_domain, limit=1)
        )
        result = {}
        for country_id in country_ids:
            pl = self.search([
                *pl_domain,
                ('country_group_ids.country_ids', '=', country_id),
            ], limit=1)
            result[country_id] = pl or pl_fallback
        result[False] = result[ctx_country.id] if ctx_country else pl_fallback
        return result