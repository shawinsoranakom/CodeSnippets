def _get_partners_values(self, country=None, grade=None, page=0, references_per_page=20, **post):
        country_all = post.pop('country_all', False)
        partner_obj = request.env['res.partner']
        country_obj = request.env['res.country']

        industries = request.env['res.partner.industry'].sudo().search([])
        industry_param = request.env['ir.http']._unslug(post.pop('industry', ''))[1]
        current_industry = industry_param in industries.ids and industries.browse(int(industry_param))

        search = post.get('search', '')

        base_partner_domain = [('is_company', '=', True), ('grade_id', '!=', False), ('website_published', '=', True), ('grade_id.active', '=', True)]
        if not request.env.user.has_group('website.group_website_restricted_editor'):
            base_partner_domain += [('grade_id.website_published', '=', True)]
        if search:
            base_partner_domain += Domain.OR(
                Domain(field, 'ilike', search)
                for field in ('name', 'website_description', 'street', 'street2', 'city', 'zip', 'state_id', 'country_id')
            )

        # Infer Country
        if not country and not country_all:
            if request.geoip.country_code:
                country = country_obj.search([('code', '=', request.geoip.country_code)], limit=1)

        # Group by country
        country_domain = list(base_partner_domain)
        if grade:
            country_domain += [('grade_id', '=', grade.id)]

        country_groups = partner_obj.sudo()._read_group(
            country_domain + [('country_id', '!=', False)],
            ["country_id"], ["__count"], order="country_id")

        # Fallback on all countries if no partners found for the country and
        # there are matching partners for other countries.
        fallback_all_countries = country and country.id not in (c.id for c, __ in country_groups)
        if fallback_all_countries:
            country = None

        # Group by grade
        grade_domain = list(base_partner_domain)
        if country:
            grade_domain += [('country_id', '=', country.id)]
        grade_groups = partner_obj.sudo()._read_group(
            grade_domain, ["grade_id"], ["__count"], order="grade_id")
        grades = [{
            'grade_id_count': sum(count for __, count in grade_groups),
            'grade_id': (0, ""),
            'active': grade is None,
        }]
        for g_grade, count in grade_groups:
            grades.append({
                'grade_id_count': count,
                'grade_id': (g_grade.id, g_grade.display_name),
                'active': grade and grade.id == g_grade.id,
            })

        countries = [{
            'country_id_count': sum(count for __, count in country_groups),
            'country_id': (0, _("All Countries")),
            'active': country is None,
        }]
        for g_country, count in country_groups:
            countries.append({
                'country_id_count': count,
                'country_id': (g_country.id, g_country.display_name),
                'active': country and g_country.id == country.id,
            })

        # current search
        if grade:
            base_partner_domain += [('grade_id', '=', grade.id)]
        if country:
            base_partner_domain += [('country_id', '=', country.id)]
        if current_industry:
            base_partner_domain += [('implemented_partner_ids.industry_id', 'in', current_industry.id)]

        # format pager
        slug = request.env['ir.http']._slug
        if grade and not country:
            url = '/partners/grade/' + slug(grade)
        elif country and not grade:
            url = '/partners/country/' + slug(country)
        elif country and grade:
            url = '/partners/grade/' + slug(grade) + '/country/' + slug(country)
        else:
            url = '/partners'
        url_args = {}
        if search:
            url_args['search'] = search
        if country_all:
            url_args['country_all'] = True
        if current_industry:
            url_args['industry'] = slug(current_industry)

        partner_count = partner_obj.sudo().search_count(base_partner_domain)
        pager = request.website.pager(
            url=url, total=partner_count, page=page, step=references_per_page, scope=7,
            url_args=url_args)

        # search partners matching current search parameters
        partner_ids = partner_obj.sudo().search(
            base_partner_domain, order="grade_sequence ASC, implemented_partner_count DESC, complete_name ASC, id ASC",
            offset=pager['offset'], limit=references_per_page)
        partners = partner_ids.sudo()

        google_maps_api_key = request.website.google_maps_api_key

        values = {
            'industries': industries,
            'current_industry': current_industry,
            'countries': countries,
            'country_all': country_all,
            'current_country': country,
            'grades': grades,
            'current_grade': grade,
            'partners': partners,
            'pager': pager,
            'searches': post,
            'search_path': "%s" % werkzeug.urls.url_encode(post),
            'search': search,
            'google_maps_api_key': google_maps_api_key,
            'fallback_all_countries': fallback_all_countries,
        }
        return values