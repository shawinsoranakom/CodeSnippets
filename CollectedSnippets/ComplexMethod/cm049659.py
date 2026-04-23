def _url_localized(cls,
            url: str | None = None,
            lang_code: str | None = None,
            canonical_domain: str | tuple[str, str, str, str, str] | None = None,
            prefetch_langs: bool = False, force_default_lang: bool = False) -> str:
        """ Returns the given URL adapted for the given lang, meaning that:

        1. It will have the lang suffixed to it
        2. The model converter parts will be translated

        If it is not possible to rebuild a path, use the current one instead.
        :func:`url_quote_plus` is applied on the returned path.

        It will also force the canonical domain is requested.

        >>> _get_url_localized(lang_fr, '/shop/my-phone-14')
        '/fr/shop/mon-telephone-14'
        >>> _get_url_localized(lang_fr, '/shop/my-phone-14', True)
        '<base_url>/fr/shop/mon-telephone-14'
        """
        if not lang_code:
            lang = request.lang
        else:
            lang = request.env['res.lang']._get_data(code=lang_code)

        if not url:
            qs = keep_query()
            url = request.httprequest.path + ('?%s' % qs if qs else '')

        # '/shop/furn-0269-chaise-de-bureau-noire-17?' to
        # '/shop/furn-0269-chaise-de-bureau-noire-17', otherwise -> 404
        url, sep, qs = url.partition('?')

        try:
            # Re-match the controller where the request path routes.
            rule, args = request.env['ir.http']._match(url)
            for key, val in list(args.items()):
                if isinstance(val, models.BaseModel):
                    if isinstance(val.env.uid, RequestUID):
                        args[key] = val = val.with_user(request.env.uid)
                    if val.env.context.get('lang') != lang.code:
                        args[key] = val = val.with_context(lang=lang.code)
                    if prefetch_langs:
                        args[key] = val = val.with_context(prefetch_langs=True)
            router = http.root.get_db_router(request.db).bind('')
            path = router.build(rule.endpoint, args)
        except (NotFound, AccessError, MissingError):
            # The build method returns a quoted URL so convert in this case for consistency.
            path = werkzeug.urls.url_quote_plus(url, safe='/')
        if force_default_lang or lang != request.env['ir.http']._get_default_lang():
            path = f'/{lang.url_code}{path if path != "/" else ""}'

        if canonical_domain:
            # canonical URLs should not have qs
            return tools.urls.urljoin(canonical_domain, path)

        return path + sep + qs