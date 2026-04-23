def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(
            r'<embed name="Video".*?src="([^"]+)"', webpage,
            'QuickTime embed', default=None)

        if video_url is None:
            flash_vars_s = self._html_search_regex(
                r'<param name="flashVars" value="([^"]+)"', webpage, 'flash vars',
                default=None)
            if not flash_vars_s:
                flash_vars_s = self._html_search_regex(
                    r'<param name="initParams" value="([^"]+)"', webpage, 'flash vars',
                    default=None)
                if flash_vars_s:
                    flash_vars_s = flash_vars_s.replace(',', '&')
            if flash_vars_s:
                flash_vars = urllib.parse.parse_qs(flash_vars_s)
                video_url_raw = urllib.parse.quote(
                    flash_vars['content'][0])
                video_url = video_url_raw.replace('http%3A', 'http:')

        if video_url is None:
            video_meta = self._html_search_meta(
                'og:video', webpage, default=None)
            if video_meta:
                video_url = self._search_regex(
                    r'src=(.*?)(?:$|&)', video_meta,
                    'meta tag video URL', default=None)

        if video_url is None:
            video_url = self._html_search_regex(
                r'MediaContentUrl["\']\s*:(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage, 'video url', default=None, group='url')

        if video_url is None:
            video_url = self._html_search_meta(
                'og:video', webpage, default=None)

        if video_url is None:
            raise ExtractorError('Cannot find video')

        title = self._og_search_title(webpage, default=None)
        if title is None:
            title = self._html_search_regex(
                [r'<b>Title:</b> ([^<]+)</div>',
                 r'class="tabSeperator">></span><span class="tabText">(.+?)<',
                 r'<title>([^<]+)</title>'],
                webpage, 'title')
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage, default=None)
        if description is None:
            description = self._html_search_meta('description', webpage)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }