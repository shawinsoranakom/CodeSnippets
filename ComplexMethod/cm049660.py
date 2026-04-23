def _url_lang(cls, path_or_uri: str, lang_code: str | None = None) -> str:
        ''' Given a relative URL, make it absolute and add the required lang or
            remove useless lang.
            Nothing will be done for absolute or invalid URL.
            If there is only one language installed, the lang will not be handled
            unless forced with `lang` parameter.

            :param lang_code: Must be the lang `code`. It could also be something
                              else, such as `'[lang]'` (used for url_return).
        '''
        Lang = request.env['res.lang']
        location = path_or_uri.strip()
        force_lang = lang_code is not None
        try:
            url = urllib.parse.urlparse(location)
        except ValueError:
            # e.g. Invalid IPv6 URL, `urllib.parse.urlparse('http://]')`
            url = False
        # relative URL with either a path or a force_lang
        if url and not url.netloc and not url.scheme and (url.path or force_lang):
            location = werkzeug.urls.url_join(request.httprequest.path, location)
            lang_url_codes = [info.url_code for info in Lang._get_frontend().values()]
            lang_code = lang_code or request.env.context['lang']
            lang_url_code = Lang._get_data(code=lang_code).url_code
            lang_url_code = lang_url_code if lang_url_code in lang_url_codes else lang_code
            if (len(lang_url_codes) > 1 or force_lang) and cls._is_multilang_url(location, lang_url_codes):
                loc, sep, qs = location.partition('?')
                ps = loc.split('/')
                default_lg = request.env['ir.http']._get_default_lang()
                if ps[1] in lang_url_codes:
                    # Replace the language only if we explicitly provide a language to url_for
                    if force_lang:
                        ps[1] = lang_url_code
                    # Remove the default language unless it's explicitly provided
                    elif ps[1] == default_lg.url_code:
                        ps.pop(1)
                # Insert the context language or the provided language
                elif lang_url_code != default_lg.url_code or force_lang:
                    ps.insert(1, lang_url_code)
                    # Remove the last empty string to avoid trailing / after joining
                    if not ps[-1]:
                        ps.pop(-1)

                location = '/'.join(ps) + sep + qs
        return location