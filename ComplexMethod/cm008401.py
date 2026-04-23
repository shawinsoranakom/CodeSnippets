def _extract_embed_urls(cls, url, webpage):
        """@returns all the embed urls on the webpage"""
        if '_EMBED_URL_RE' not in cls.__dict__:
            assert isinstance(cls._EMBED_REGEX, (list, tuple))
            for idx, regex in enumerate(cls._EMBED_REGEX):
                assert regex.count('(?P<url>') == 1, \
                    f'{cls.__name__}._EMBED_REGEX[{idx}] must have exactly 1 url group\n\t{regex}'
            cls._EMBED_URL_RE = tuple(map(re.compile, cls._EMBED_REGEX))

        for regex in cls._EMBED_URL_RE:
            for mobj in regex.finditer(webpage):
                embed_url = urllib.parse.urljoin(url, unescapeHTML(mobj.group('url')))
                if cls._VALID_URL is False or cls.suitable(embed_url):
                    yield embed_url