def check_existing_page(self, page):
        """
            Returns a boolean, whether the page is considered to exist for the
            current website. This is a heuristic and is not perfectly reliable.
        """
        # The page exists if there is a 'website.page' record with this url
        if len(self._get_website_pages(domain=[('url', '=', page), ('view_id', '!=', False)], limit=1)) > 0:
            return True

        # The page is considered to exist if there is a 'website.rewrite' record
        # that does a redirect 301 or 302, for simplicity we do not check
        # further whether the redirection points to an existing url.
        redirects_domain = self.get_current_website().website_domain() & Domain(
            [('url_from', '=', page), ('redirect_type', 'in', ('301', '302'))]
        )
        if len(self.env['website.rewrite'].search(redirects_domain, limit=1)) > 0:
            return True

        router = self.env['ir.http'].routing_map().bind('')
        # If there is no rules matching this page, it does not exists
        if not router.test(path_info=page, method='GET'):
            return False

        try:
            rule, args = router.match(page, method='GET', return_rule=True)
        except werkzeug.routing.RequestRedirect:
            # The page is considered to exist if it redirects (this happens if
            # there is a 'website.rewrite' 308), for simplicity we do not check
            # further whether the redirection points to an existing url.
            return True

        try:
            # The rule may have restriction for some records that appear in its
            # url, these are checked by `rule.build`.
            for arg in args:
                if isinstance(args[arg], models.BaseModel):
                    # Models from `router.match` are missing users in their env
                    args[arg] = args[arg].with_user(self.env.uid)
                    # For record that may be related to a website, we skip them
                    # if they are for a different website than the current one
                    if hasattr(args[arg], 'website_id') and args[arg].website_id and args[arg].website_id != self:
                        return False
            rule.build(args, append_unknown=False)
        except MissingError:
            return False
        return True