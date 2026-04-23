def _real_extract(self, url):
        m_url = re.match(self._VALID_URL, url)
        video_id = m_url.group('id')
        blog = m_url.group('blog_name')

        url = 'http://%s.tumblr.com/post/%s/' % (blog, video_id)
        webpage, urlh = self._download_webpage_handle(url, video_id)

        redirect_url = urlh.geturl()
        if 'tumblr.com/safe-mode' in redirect_url or redirect_url.startswith('/safe-mode'):
            raise ExtractorError(
                'This Tumblr may contain sensitive media. '
                'Disable safe mode in your account settings '
                'at https://www.tumblr.com/settings/account#safe_mode',
                expected=True)

        iframe_url = self._search_regex(
            r'src=\'(https?://www\.tumblr\.com/video/[^\']+)\'',
            webpage, 'iframe url', default=None)
        if iframe_url is None:
            return self.url_result(redirect_url, 'Generic')

        iframe = self._download_webpage(iframe_url, video_id, 'Downloading iframe page')

        duration = None
        sources = []

        sd_url = self._search_regex(
            r'<source[^>]+src=(["\'])(?P<url>.+?)\1', iframe,
            'sd video url', default=None, group='url')
        if sd_url:
            sources.append((sd_url, 'sd'))

        options = self._parse_json(
            self._search_regex(
                r'data-crt-options=(["\'])(?P<options>.+?)\1', iframe,
                'hd video url', default='', group='options'),
            video_id, fatal=False)
        if options:
            duration = int_or_none(options.get('duration'))
            hd_url = options.get('hdUrl')
            if hd_url:
                sources.append((hd_url, 'hd'))

        formats = [{
            'url': video_url,
            'ext': 'mp4',
            'format_id': format_id,
            'height': int_or_none(self._search_regex(
                r'/(\d{3,4})$', video_url, 'height', default=None)),
            'quality': quality,
        } for quality, (video_url, format_id) in enumerate(sources)]

        self._sort_formats(formats)

        # The only place where you can get a title, it's not complete,
        # but searching in other places doesn't work for all videos
        video_title = self._html_search_regex(
            r'(?s)<title>(?P<title>.*?)(?: \| Tumblr)?</title>',
            webpage, 'title')

        return {
            'id': video_id,
            'title': video_title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
        }