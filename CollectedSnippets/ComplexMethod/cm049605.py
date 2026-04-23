def get_current_website(self, fallback=True):
        """ The current website is returned in the following order:

        - the website forced in session `force_website_id`
        - the website set in context
        - (if frontend or fallback) the website matching the request's "domain"
        - arbitrary the first website found in the database if `fallback` is set
          to `True`
        - empty browse record
        """
        is_frontend_request = request and getattr(request, 'is_frontend', False)
        if request and request.session.get('force_website_id'):
            website_id = self.browse(request.session['force_website_id']).exists()
            if not website_id:
                # Don't crash is session website got deleted
                request.session.pop('force_website_id')
            else:
                return website_id

        website_id = self.env.context.get('website_id')
        if website_id:
            return self.browse(website_id)

        if not is_frontend_request and not fallback:
            # It's important than backend requests with no fallback requested
            # don't go through
            return self.browse(False)

        # Reaching this point means that:
        # - We didn't find a website in the session or in the context.
        # - And we are either:
        #   - in a frontend context
        #   - in a backend context (or early in the dispatch stack) and a
        #     fallback website is requested.
        # We will now try to find a website matching the request host/domain (if
        # there is one on request) or return a random one.

        # The format of `httprequest.host` is `domain:port`
        domain_name = (
            request and request.httprequest.host
            or hasattr(threading.current_thread(), 'url') and threading.current_thread().url
            or '')
        website_id = self.sudo()._get_current_website_id(domain_name, fallback=fallback)
        return self.browse(website_id)