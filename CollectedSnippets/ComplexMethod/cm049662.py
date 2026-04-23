def _match(cls, path):
        """
        Grant multilang support to URL matching by using http 3xx
        redirections and URL rewrite. This method also grants various
        attributes such as ``lang`` and ``is_frontend`` on the current
        ``request`` object.

        1/ Use the URL as-is when it matches a non-multilang compatible
           endpoint.

        2/ Use the URL as-is when the lang is not present in the URL and
           that the default lang has been requested.

        3/ Use the URL as-is saving the requested lang when the user is
           a bot and that the lang is missing from the URL.

        4) Use the url as-is when the lang is missing from the URL, that
           another lang than the default one has been requested but that
           it is forbidden to redirect (e.g. POST)

        5/ Redirect the browser when the lang is missing from the URL
           but another lang than the default one has been requested. The
           requested lang is injected before the original path.

        6/ Redirect the browser when the lang is present in the URL but
           it is the default lang. The lang is removed from the original
           URL.

        7/ Redirect the browser when the lang present in the URL is an
           alias of the preferred lang url code (e.g. fr_FR -> fr)

        8/ Redirect the browser when the requested page is the homepage
           but that there is a trailing slash.

        9/ Rewrite the URL when the lang is present in the URL, that it
           matches and that this lang is not the default one. The URL is
           rewritten to remove the lang.

        Note: The "requested lang" is (in order) either (1) the lang in
              the URL or (2) the lang in the ``frontend_lang`` request
              cookie or (3) the lang in the context or (4) the default
              lang of the website.
        """

        # The URL has been rewritten already
        if hasattr(request, 'is_frontend'):
            return super()._match(path)

        # See /1, match a non website endpoint
        try:
            rule, args = super()._match(path)
            routing = rule.endpoint.routing
            request.is_frontend = routing.get('website', False)
            request.is_frontend_multilang = request.is_frontend and routing.get('multilang', routing['type'] == 'http')
            if not request.is_frontend:
                return rule, args
        except NotFound:
            _, url_lang_str, *rest = path.split('/', 2)
            path_no_lang = '/' + (rest[0] if rest else '')
        else:
            url_lang_str = ''
            path_no_lang = path

        allow_redirect = (
            request.httprequest.method != 'POST'
            and getattr(request, 'is_frontend_multilang', True)
        )

        # Some URLs in website are concatenated, first url ends with /,
        # second url starts with /, resulting url contains two following
        # slashes that must be merged.
        if allow_redirect and '//' in path:
            new_url = path.replace('//', '/')
            werkzeug.exceptions.abort(request.redirect(new_url, code=301, local=True))

        # There is no user on the environment yet but the following code
        # requires one to set the lang on the request. Temporary grant
        # the public user. Don't try it at home!
        real_env = request.env
        try:
            request.registry['ir.http']._auth_method_public()  # it calls update_env
            nearest_url_lang = request.env['ir.http'].get_nearest_lang(request.env['res.lang']._get_data(url_code=url_lang_str).code or url_lang_str)
            cookie_lang = request.env['ir.http'].get_nearest_lang(request.cookies.get('frontend_lang'))
            context_lang = request.env['ir.http'].get_nearest_lang(real_env.context.get('lang'))
            default_lang = cls._get_default_lang()
            request.lang = request.env['res.lang']._get_data(code=(
                nearest_url_lang or cookie_lang or context_lang or default_lang.code
            ))
            request_url_code = request.lang.url_code
        finally:
            request.env = real_env

        if not nearest_url_lang:
            url_lang_str = None

        # See /2, no lang in url and default website
        if not url_lang_str and request.lang == default_lang:
            _logger.debug("%r (lang: %r) no lang in url and default website, continue", path, request_url_code)

        # See /3, missing lang in url but user-agent is a bot
        elif not url_lang_str and request.env['ir.http'].is_a_bot():
            _logger.debug("%r (lang: %r) missing lang in url but user-agent is a bot, continue", path, request_url_code)
            request.lang = default_lang

        # See /4, no lang in url and should not redirect (e.g. POST), continue
        elif not url_lang_str and not allow_redirect:
            _logger.debug("%r (lang: %r) no lang in url and should not redirect (e.g. POST), continue", path, request_url_code)

        # See /5, missing lang in url, /home -> /fr/home
        elif not url_lang_str:
            _logger.debug("%r (lang: %r) missing lang in url, redirect", path, request_url_code)
            redirect = request.redirect_query(f'/{request_url_code}{path}', request.httprequest.args)
            redirect.set_cookie('frontend_lang', request.lang.code)
            werkzeug.exceptions.abort(redirect)

        # See /6, default lang in url, /en/home -> /home
        elif url_lang_str == default_lang.url_code and allow_redirect:
            _logger.debug("%r (lang: %r) default lang in url, redirect", path, request_url_code)
            redirect = request.redirect_query(path_no_lang, request.httprequest.args)
            redirect.set_cookie('frontend_lang', default_lang.code)
            werkzeug.exceptions.abort(redirect)

        # See /7, lang alias in url, /fr_FR/home -> /fr/home
        elif url_lang_str != request_url_code and allow_redirect:
            _logger.debug("%r (lang: %r) lang alias in url, redirect", path, request_url_code)
            redirect = request.redirect_query(f'/{request_url_code}{path_no_lang}', request.httprequest.args, code=301)
            redirect.set_cookie('frontend_lang', request.lang.code)
            werkzeug.exceptions.abort(redirect)

        # See /8, homepage with trailing slash. /fr_BE/ -> /fr_BE
        elif path == f'/{url_lang_str}/' and allow_redirect:
            _logger.debug("%r (lang: %r) homepage with trailing slash, redirect", path, request_url_code)
            redirect = request.redirect_query(path[:-1], request.httprequest.args, code=301)
            redirect.set_cookie('frontend_lang', default_lang.code)
            werkzeug.exceptions.abort(redirect)

        # See /9, valid lang in url
        elif url_lang_str == request_url_code:
            # Rewrite the URL to remove the lang
            _logger.debug("%r (lang: %r) valid lang in url, rewrite url and continue", path, request_url_code)
            request.reroute(path_no_lang)
            path = path_no_lang

        else:
            _logger.warning("%r (lang: %r) couldn't not correctly route this frontend request, url used as-is.", path, request_url_code)

        # Re-match using rewritten route and really raise for 404 errors
        try:
            rule, args = super()._match(path)
            routing = rule.endpoint.routing
            request.is_frontend = routing.get('website', False)
            request.is_frontend_multilang = request.is_frontend and routing.get('multilang', routing['type'] == 'http')
            return rule, args
        except NotFound:
            # Use website to render a nice 404 Not Found html page
            request.is_frontend = True
            request.is_frontend_multilang = True
            raise