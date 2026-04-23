def sitemap_shop(env, rule, qs):
        website = env['website'].get_current_website()
        if website and website.ecommerce_access == 'logged_in' and not qs:
            # Make sure urls are not listed in sitemap when restriction is active
            # and no autocomplete query string is provided
            return

        if not qs or qs.lower() in SHOP_PATH:
            yield {'loc': SHOP_PATH}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, f'{SHOP_PATH}/category', Category._rec_name)
        dom &= website.website_domain()
        for cat in Category.search(dom):
            loc = f'{SHOP_PATH}/category/{env["ir.http"]._slug(cat)}'
            if not qs or qs.lower() in loc:
                yield {'loc': loc}