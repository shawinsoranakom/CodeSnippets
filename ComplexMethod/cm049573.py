def index(self, **kw):
        """ The goal of this controller is to make sure we don't serve a 404 as
        the website homepage. As this is the website entry point, serving a 404
        is terrible.
        There is multiple fallback mechanism to prevent that:
        - If homepage URL is set (empty by default), serve the website.page
        matching it
        - If homepage URL is set (empty by default), serve the controller
        matching it
        - If homepage URL is not set, serve the `/` website.page
        - Serve the first accessible menu as last resort. It should be relevant
        content, at least better than a 404
        - Serve 404
        Most DBs will just have a website.page with '/' as URL and keep the
        homepage_url setting empty.
        """
        homepage_url = request.website._get_cached('homepage_url')
        if homepage_url and homepage_url != '/':
            request.reroute(homepage_url)

        # Check for page
        website_page = request.env['ir.http']._serve_page()
        if website_page:
            return website_page

        # Check for controller
        if homepage_url and homepage_url != '/':
            try:
                rule, args = request.env['ir.http']._match(homepage_url)
                return request._serve_ir_http(rule, args)
            except (AccessError, NotFound, SessionExpiredException):
                pass

        # Fallback on first accessible menu
        def is_reachable(menu):
            return menu.is_visible and menu.url not in ('/', '', '#') and not menu.url.startswith(('/?', '/#', ' '))

        # prefetch all menus (it will prefetch website.page too)
        top_menu = request.website.menu_id

        reachable_menus = top_menu.child_id.filtered(is_reachable)
        if reachable_menus:
            return request.redirect(reachable_menus[0].url)

        raise request.not_found()