def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)

        if request.is_frontend:
            cls._frontend_pre_dispatch()

            # update the context of "<model(...):...>" args
            for key, val in list(args.items()):
                if isinstance(val, models.BaseModel):
                    args[key] = val.with_context(request.env.context)

        if request.is_frontend_multilang:
            # A product with id 1 and named 'egg' is accessible via a
            # frontend multilang enpoint 'foo' at the URL '/foo/1'.
            # The preferred URL to access the product (and to generate
            # URLs pointing it) should instead be the sluggified URL
            # '/foo/egg-1'. This code is responsible of redirecting the
            # browser from '/foo/1' to '/foo/egg-1', or '/fr/foo/1' to
            # '/fr/foo/oeuf-1'. While it is nice (for humans) to have a
            # pretty URL, the real reason of this redirection is SEO.
            if request.httprequest.method in ('GET', 'HEAD'):
                _, path = rule.build(args)
                assert path is not None
                generated_path = werkzeug.urls.url_unquote_plus(path)
                current_path = werkzeug.urls.url_unquote_plus(request.httprequest.path)
                if generated_path != current_path:
                    if request.lang != cls._get_default_lang():
                        path = f'/{request.lang.url_code}{path}'
                    redirect = request.redirect_query(path, request.httprequest.args, code=301)
                    werkzeug.exceptions.abort(redirect)