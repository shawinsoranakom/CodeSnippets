def sitemap_industry(env, rule, qs):
        if not qs or qs.lower() in '/customers':
            yield {'loc': '/customers'}

        Industry = env['res.partner.industry']
        dom = sitemap_qs2dom(qs, '/customers/industry', Industry._rec_name)
        for industry in Industry.search(dom):
            loc = '/customers/industry/%s' % env['ir.http']._slug(industry)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

        dom = [('website_published', '=', True), ('assigned_partner_id', '!=', False), ('country_id', '!=', False)]
        dom += sitemap_qs2dom(qs, '/customers/country')
        countries = env['res.partner'].sudo()._read_group(dom, ['country_id'])
        for [country] in countries:
            loc = '/customers/country/%s' % env['ir.http']._slug(country)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}