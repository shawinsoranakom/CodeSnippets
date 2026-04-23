def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, expected_status=429)
        if '>Rate Limit Exceeded' in webpage:
            raise ExtractorError(
                '[%s] %s: %s' % (self.IE_NAME, video_id, 'You are suspected as a bot. Wait, or pass the captcha test on the site and provide --cookies.'),
                expected=True)

        title = self._html_search_regex(r'(?s)<h1\b[^>]*>(.+?)</h1>', webpage, 'title')

        display_id = video_id
        video_id = self._search_regex(r'(?s)<video\b[^>]+\bdata-id\s*=\s*["\']?([\w-]+)', webpage, 'short video ID')
        srcs = self._download_json(
            'https://%s/v-alt/%s' % (self._DOMAIN, video_id), video_id,
            note='Downloading list of source files')
        formats = [{
            'url': f_url,
            'format_id': f_id,
            'height': int_or_none(f_id),
        } for f_url, f_id in (
            (url_or_none(f_v), f_match.group(1))
            for f_v, f_match in (
                (v, re.match(r'^data-src(\d{3,})$', k))
                for k, v in srcs.items() if v) if f_match)
            if f_url
        ]
        if not formats:
            formats = [{'url': url} for url in srcs.values()]
        self._sort_formats(formats)

        info = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        info.pop('url', None)
        # may not have found the thumbnail if it was in a list in the ld+json
        info.setdefault('thumbnail', self._og_search_thumbnail(webpage))
        detail = self._get_detail(webpage) or ''
        info['description'] = self._html_search_regex(
            r'(?s)(.+?)(?:%s\s*<|<ul\b)' % (re.escape(info.get('description', '')), ),
            detail, 'description', default=None) or None
        info['title'] = re.sub(r'\s*[,-][^,-]+$', '', info.get('title') or title) or self._generic_title(url)

        def cat_tags(name, html):
            l = self._html_search_regex(
                r'(?s)<span\b[^>]*>\s*%s\s*:\s*</span>(.+?)</li>' % (re.escape(name), ),
                html, name, default='')
            return [x for x in re.split(r'\s+', l) if x]

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'age_limit': 18,
            'formats': formats,
            'categories': cat_tags('Categories', detail),
            'tags': cat_tags('Tags', detail),
            'uploader': self._html_search_regex(r'[Uu]ploaded\s+by\s(.+?)"', webpage, 'uploader', default=None),
        }, info)