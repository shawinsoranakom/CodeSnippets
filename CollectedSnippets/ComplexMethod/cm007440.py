def _real_extract(self, url):
        # /play/ URLs provide embedded video URL and more metadata
        url = url.replace('/embed/', '/play/')
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        error_msg = self._search_regex(
            r'<div id="error-message-content">([^<]+)',
            webpage, 'error message', default=None)
        if error_msg:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_msg),
                expected=True)

        media_info = self._parse_json(self._search_regex(
            r'var\s+mediaInfo\s*=\s*({.*});', webpage, 'media info'), video_id)

        video_id = media_info['MEDIA_ID']

        formats = []
        for key in ('html5Url', 'html5HQUrl'):
            video_url = media_info.get(key)
            if not video_url:
                continue
            format_id = self._search_regex(
                r'\bq=(.+?)\b', video_url, 'format id', default=None)
            formats.append({
                'url': video_url,
                'ext': 'mp4' if format_id.isnumeric() else format_id,
                'format_id': format_id,
                'height': int(format_id) if format_id.isnumeric() else None,
            })
        self._sort_formats(formats)

        timestamp = media_info.get('PUBLISH_DATETIME')
        if timestamp:
            timestamp = parse_iso8601(timestamp + ' +0800', ' ')

        category = media_info.get('catName')
        categories = [category] if category else []

        uploader = media_info.get('NICKNAME')
        uploader_url = None

        author_div = get_element_by_attribute('itemprop', 'author', webpage)
        if author_div:
            uploader = uploader or self._html_search_meta('name', author_div)
            uploader_url = self._html_search_regex(
                r'<link[^>]+itemprop="url"[^>]+href="([^"]+)"', author_div,
                'uploader URL', fatal=False)

        return {
            'id': video_id,
            'title': media_info['TITLE'],
            'description': remove_end(media_info.get('metaDesc'), ' (Xuite 影音)'),
            'thumbnail': media_info.get('ogImageUrl'),
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': media_info.get('MEMBER_ID'),
            'uploader_url': uploader_url,
            'duration': float_or_none(media_info.get('MEDIA_DURATION'), 1000000),
            'categories': categories,
            'formats': formats,
        }