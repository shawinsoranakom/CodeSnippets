def _real_extract(self, url):
        host, playlist_id = re.match(self._VALID_URL, url).groups()

        if host == 'cocoro.tv':
            webpage = self._download_webpage(url, playlist_id)

            entries = []

            for mobj in re.finditer(
                    r'<a[^>]+href=(["\'])(?P<url>%s.*?)\1[^>]*>' % AsianCrushIE._VALID_URL,
                    webpage):
                attrs = extract_attributes(mobj.group(0))
                if attrs.get('class') == 'clearfix':
                    entries.append(self.url_result(
                        mobj.group('url'), ie=AsianCrushIE.ie_key()))

            title = self._html_search_regex(
                r'(?s)<h1\b[^>]\bid=["\']movieTitle[^>]+>(.+?)</h1>', webpage,
                'title', default=None) or self._og_search_title(
                webpage, default=None) or self._html_search_meta(
                'twitter:title', webpage, 'title',
                default=None) or self._search_regex(
                r'<title>([^<]+)</title>', webpage, 'title', fatal=False)
            if title:
                title = re.sub(r'\s*\|\s*.+?$', '', title)

            description = self._og_search_description(
                webpage, default=None) or self._html_search_meta(
                'twitter:description', webpage, 'description', fatal=False)
        else:
            show = self._download_object_data(host, playlist_id, 'show')
            title = show.get('name')
            description = self._get_object_description(show)
            entries = OnDemandPagedList(
                functools.partial(self._fetch_page, host, playlist_id),
                self._PAGE_SIZE)

        return self.playlist_result(entries, playlist_id, title, description)