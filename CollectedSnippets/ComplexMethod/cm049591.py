def _url_for(cls, url_from: str, lang_code: str | None = None) -> str:
        ''' Return the url with the rewriting applied.
            Nothing will be done for absolute URL, invalid URL, or short URL from 1 char.

            :param url_from: The URL to convert.
            :param lang_code: Must be the lang `code`. It could also be something
                              else, such as `'[lang]'` (used for url_return).
        '''
        path, sep, qs = (url_from or '').partition('?')

        if not qs:
            path, sep, qs = (url_from or '').partition('#')

        if (
            path
            # don't try to match route if we know that no rewrite has been loaded.
            and request.env['ir.http']._rewrite_len(request.website_routing)
            and (
                len(path) > 1
                and path.startswith('/')
                and '/static/' not in path
                and not path.startswith('/web/')
            )
        ):
            url_from, _ = request.env['ir.http'].url_rewrite(path)
            url_from = url_from if not qs else f"{url_from}{sep}{qs}"

        return super()._url_for(url_from, lang_code)