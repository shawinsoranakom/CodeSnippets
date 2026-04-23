def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id, display_id = mobj.group('id', 'display_id')

        webpage = self._download_webpage(url, display_id)

        title = self._search_regex(
            r'<h1>([^<]+)', webpage, 'title',
            default=None) or self._html_search_meta(
            'ya:ovs:original_name', webpage, 'title', fatal=True)

        loc = self._search_regex(
            r'PCTMLOC\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage, 'loc',
            group='value')

        loc_b64 = ''
        for c in loc:
            c_ord = ord(c)
            if ord('a') <= c_ord <= ord('z') or ord('A') <= c_ord <= ord('Z'):
                upper = ord('Z') if c_ord <= ord('Z') else ord('z')
                c_ord += 13
                if upper < c_ord:
                    c_ord -= 26
            loc_b64 += chr(c_ord)

        video_url = base64.b64decode(loc_b64).decode('utf-8')

        description = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']pt-movie-desc[^>]+>(.+?)</div>', webpage,
            'description', fatal=False)

        thumbnail = self._search_regex(
            r'<img[^>]+class=["\']video-preview[^>]+\bsrc=(["\'])(?P<value>(?:(?!\1).)+)\1',
            webpage, 'thumbnail', default=None,
            group='value') or self._og_search_thumbnail(webpage)

        creator = self._html_search_meta(
            'video:director', webpage, 'creator', default=None)

        release_date = self._html_search_meta(
            'video:release_date', webpage, default=None)
        if release_date:
            release_date = release_date.replace('-', '')

        def int_meta(name):
            return int_or_none(self._html_search_meta(
                name, webpage, default=None))

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'creator': creator,
            'release_date': release_date,
            'duration': int_meta('video:duration'),
            'tbr': int_meta('ya:ovs:bitrate'),
            'width': int_meta('og:video:width'),
            'height': int_meta('og:video:height'),
            'http_headers': {
                'Referer': url,
            },
        }