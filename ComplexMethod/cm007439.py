def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(
            webpage, default=None) or self._html_search_meta(
            'title', webpage, default=None) or self._search_regex(
            r'<title>([^<]+)<', webpage, 'title')
        title = re.sub(r'\s*-\s*TV Net\s*$', '', title)

        if '/video/' in url or '/radio/' in url:
            is_live = False
        elif '/kenh-truyen-hinh/' in url:
            is_live = True
        else:
            is_live = None

        data_file = unescapeHTML(self._search_regex(
            r'data-file=(["\'])(?P<url>(?:https?:)?//.+?)\1', webpage,
            'data file', group='url'))

        stream_urls = set()
        formats = []
        for stream in self._download_json(data_file, video_id):
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('url'))
            if stream_url in stream_urls or not stream_url:
                continue
            stream_urls.add(stream_url)
            formats.extend(self._extract_m3u8_formats(
                stream_url, video_id, 'mp4',
                entry_protocol='m3u8' if is_live else 'm3u8_native',
                m3u8_id='hls', fatal=False))
        self._sort_formats(formats)

        # better support for radio streams
        if title.startswith('VOV'):
            for f in formats:
                f.update({
                    'ext': 'm4a',
                    'vcodec': 'none',
                })

        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or unescapeHTML(
            self._search_regex(
                r'data-image=(["\'])(?P<url>(?:https?:)?//.+?)\1', webpage,
                'thumbnail', default=None, group='url'))

        if is_live:
            title = self._live_title(title)

        view_count = int_or_none(self._search_regex(
            r'(?s)<div[^>]+\bclass=["\'].*?view-count[^>]+>.*?(\d+).*?</div>',
            webpage, 'view count', default=None))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'is_live': is_live,
            'view_count': view_count,
            'formats': formats,
        }