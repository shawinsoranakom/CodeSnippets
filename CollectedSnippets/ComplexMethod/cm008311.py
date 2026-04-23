def _real_extract(self, url):
        host, video_id, tmp_id, display_id, embed_id = self._match_valid_url(url).group(
            'host', 'id', 'tmp_id', 'display_id', 'embed_id')
        webpage = self._download_webpage(url, video_id or tmp_id, fatal=False) or ''

        if not video_id:
            video_id = embed_id or self._html_search_regex(
                rf'src="https?://{host}/media/embed.*(?:\?|&)key=([0-9a-f]+)&?',
                webpage, 'video_id')

        if not (display_id or tmp_id):
            # Title, description from embedded page's meta wouldn't be correct
            title = self._html_search_regex(r'<video-js[^>]* data-piwik-title="([^"<]+)"', webpage, 'title', fatal=False)
            description = None
            thumbnail = None
        else:
            title = self._html_search_meta(('og:title', 'twitter:title', 'title'), webpage, fatal=False)
            description = self._html_search_meta(
                ('og:description', 'twitter:description', 'description'), webpage, fatal=False)
            thumbnail = self._html_search_meta(('og:image', 'twitter:image'), webpage, fatal=False)

        formats, subtitles = [], {}
        try:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                f'https://{host}/media/hlsMedium/key/{video_id}/format/auto/ext/mp4/learning/0/path/m3u8',
                video_id, 'mp4', m3u8_id='hls', fatal=True)
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError) or e.cause.status not in (404, 500):
                raise

        formats.append({'url': f'https://{host}/getMedium/{video_id}.mp4'})

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
        }