def _is_multilang_url(cls, local_url: str, lang_url_codes: list[str] | None = None) -> bool:
        ''' Check if the given URL content is supposed to be translated.
            To be considered as translatable, the URL should either:
            1. Match a POST (non-GET actually) controller that is `website=True` and
            either `multilang` specified to True or if not specified, with `type='http'`.
            2. If not matching 1., everything not under /static/ or /web/ will be translatable
        '''
        if not lang_url_codes:
            lang_url_codes = [lg.url_code for lg in request.env['res.lang']._get_frontend().values()]
        spath = local_url.split('/')
        # if a language is already in the path, remove it
        if spath[1] in lang_url_codes:
            spath.pop(1)
            local_url = '/'.join(spath)

        url = local_url.partition('#')[0].split('?')
        path = url[0]

        # Consider /static/ and /web/ files as non-multilang
        if '/static/' in path or path.startswith('/web/'):
            return False

        query_string = url[1] if len(url) > 1 else None

        # Try to match an endpoint in werkzeug's routing table
        try:
            _, func = request.env['ir.http'].url_rewrite(path, query_args=query_string)

            # /page/xxx has no endpoint/func but is multilang
            return (not func or (
                func.routing.get('website', False)
                and func.routing.get('multilang', func.routing['type'] == 'http')
            ))
        except Exception as exception:  # noqa: BLE001
            _logger.warning(exception)
            return False