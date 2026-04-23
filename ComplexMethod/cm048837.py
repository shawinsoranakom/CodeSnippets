def customers(self, country=None, industry=None, page=0, **post):
        Tag = request.env['res.partner.tag']
        Partner = request.env['res.partner']
        search_value = post.get('search')

        domain = [('website_published', '=', True), ('assigned_partner_id', '!=', False)]
        if search_value:
            domain += [
                '|', '|',
                ('name', 'ilike', search_value),
                ('website_description', 'ilike', search_value),
                ('industry_id.name', 'ilike', search_value),
            ]

        tag_id = post.get('tag_id')
        if tag_id:
            tag_id = request.env['ir.http']._unslug(tag_id)[1] or 0
            domain += [('website_tag_ids', 'in', tag_id)]

        # group by industry, based on customers found with the search(domain)
        industry_groups = Partner.sudo()._read_group(
            domain, ["industry_id"], ["__count"], order="industry_id")

        if industry:
            domain.append(('industry_id', '=', industry.id))
            if not any(ind.id == industry.id for ind, __ in industry_groups) and industry.exists():
                industry_groups.append((industry, 0))
                industry_groups = sorted(industry_groups, key=lambda group: group[0].name or '')

        industries = [{
            'industry_id_count': sum(count for __, count, in industry_groups),
            'industry_id': (0, _("All Industries")),
        }]
        for g_industry, count in industry_groups:
            industries.append({
                'industry_id_count': count,
                'industry_id': g_industry and (g_industry.id, g_industry.display_name),
            })

        # group by country, based on customers found with the search(domain)
        country_groups = Partner.sudo()._read_group(domain, ["country_id"], ["__count"], order="country_id")

        fallback_all_countries = False
        if country:
            if country_groups and country.id not in (country.id for country, __ in country_groups):
                # fallback on all countries if no customer found for the country
                # and there are matching customers for other countries
                fallback_all_countries = True
                country = None
            else:
                domain += [('country_id', '=', country.id)]

        countries = [{
            'country_id_count': sum(count for __, count in country_groups),
            'country_id': (0, _("All Countries")),
        }]
        for g_country, count in country_groups:
            countries.append({
                'country_id_count': count,
                'country_id': g_country and (g_country.id, g_country.sudo().display_name),
            })

        # search customers to display
        partner_count = Partner.sudo().search_count(domain)

        # pager
        url = '/customers'
        if industry:
            url += '/industry/%s' % industry.id
        if country:
            url += '/country/%s' % country.id
        pager = request.website.pager(
            url=url, total=partner_count, page=page, step=self._references_per_page,
            scope=7, url_args=post
        )

        partners = Partner.sudo().search(domain, offset=pager['offset'], limit=self._references_per_page)
        google_maps_api_key = request.website.google_maps_api_key

        tags = Tag.search([('website_published', '=', True), ('partner_ids', 'in', partners.ids)], order='classname, name ASC')
        tag = tag_id and Tag.browse(tag_id) or False

        values = {
            'countries': countries,
            'current_country_id': country.id if country and partners else 0,
            'current_country': country if partners and country else False,
            'industries': industries,
            'current_industry_id': industry.id if industry else 0,
            'current_industry': industry or False,
            'partners': partners,
            'pager': pager,
            'post': post,
            'search_path': "?%s" % werkzeug.urls.url_encode(post),
            'tag': tag,
            'tags': tags,
            'google_maps_api_key': google_maps_api_key,
            'fallback_all_countries': fallback_all_countries,
        }
        return request.render("website_customer.index", values)