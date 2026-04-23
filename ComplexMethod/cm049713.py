def sitemap_partners(env, rule, qs):
        if not qs or qs.lower() in '/partners':
            yield {'loc': '/partners'}

        slug = env['ir.http']._slug
        base_partner_domain = [
            ('is_company', '=', True),
            ('grade_id', '!=', False),
            ('website_published', '=', True),
            ('grade_id.website_published', '=', True),
            ('grade_id.active', '=', True),
        ]
        grades = env['res.partner'].sudo()._read_group(base_partner_domain, groupby=['grade_id'])
        for [grade] in grades:
            loc = '/partners/grade/%s' % slug(grade)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}
        country_partner_domain = base_partner_domain + [('country_id', '!=', False)]
        countries = env['res.partner'].sudo()._read_group(country_partner_domain, groupby=['country_id'])
        for [country] in countries:
            loc = '/partners/country/%s' % slug(country)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}