def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        def extract_title(default=NO_DEFAULT):
            title = self._html_search_meta(
                ('fulltitle', 'title'), webpage, default=None)
            if not title or title == "c't":
                title = self._search_regex(
                    r'<div[^>]+class="videoplayerjw"[^>]+data-title="([^"]+)"',
                    webpage, 'title', default=None)
            if not title:
                title = self._html_search_regex(
                    r'<h1[^>]+\bclass=["\']article_page_title[^>]+>(.+?)<',
                    webpage, 'title', default=default)
            return title

        title = extract_title(default=None)
        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'description', webpage)

        def _make_kaltura_result(kaltura_url):
            return {
                '_type': 'url_transparent',
                'url': smuggle_url(kaltura_url, {'source_url': url}),
                'ie_key': KalturaIE.ie_key(),
                'title': title,
                'description': description,
            }

        kaltura_url = KalturaIE._extract_url(webpage)
        if kaltura_url:
            return _make_kaltura_result(kaltura_url)

        kaltura_id = self._search_regex(
            r'entry-id=(["\'])(?P<id>(?:(?!\1).)+)\1', webpage, 'kaltura id',
            default=None, group='id')
        if kaltura_id:
            return _make_kaltura_result(f'kaltura:2238431:{kaltura_id}')

        yt_urls = tuple(YoutubeIE._extract_embed_urls(url, webpage))
        if yt_urls:
            return self.playlist_from_matches(
                yt_urls, video_id, title, ie=YoutubeIE.ie_key())

        title = extract_title()
        api_params = urllib.parse.parse_qs(
            self._search_regex(r'/videout/feed\.json\?([^\']+)', webpage, 'feed params', default=None) or '')
        if not api_params or 'container' not in api_params or 'sequenz' not in api_params:
            container_id = self._search_regex(
                r'<div class="videoplayerjw"[^>]+data-container="([0-9]+)"',
                webpage, 'container ID')

            sequenz_id = self._search_regex(
                r'<div class="videoplayerjw"[^>]+data-sequenz="([0-9]+)"',
                webpage, 'sequenz ID')
            api_params = {
                'container': container_id,
                'sequenz': sequenz_id,
            }
        doc = self._download_xml(
            'http://www.heise.de/videout/feed', video_id, query=api_params)

        formats = []
        for source_node in doc.findall('.//{http://rss.jwpcdn.com/}source'):
            label = source_node.attrib['label']
            height = int_or_none(self._search_regex(
                r'^(.*?_)?([0-9]+)p$', label, 'height', default=None))
            video_url = source_node.attrib['file']
            ext = determine_ext(video_url, '')
            formats.append({
                'url': video_url,
                'format_note': label,
                'format_id': f'{ext}_{label}',
                'height': height,
            })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': (xpath_text(doc, './/{http://rss.jwpcdn.com/}image')
                          or self._og_search_thumbnail(webpage)),
            'timestamp': parse_iso8601(
                self._html_search_meta('date', webpage)),
            'formats': formats,
        }