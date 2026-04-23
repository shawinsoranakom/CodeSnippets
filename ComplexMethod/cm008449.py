def _real_extract(self, url):
        domain, video_id = self._match_valid_url(url).group('domain', 'id')
        webpage = self._download_webpage(url, video_id, expected_status=429)
        if '>Rate Limit Exceeded' in webpage:
            raise ExtractorError(
                f'You are suspected as a bot. Wait, or pass the captcha on the site and provide cookies. {self._login_hint()}',
                video_id=video_id, expected=True)

        title = self._html_search_regex(r'(?s)<h1\b[^>]*>(.+?)</h1>', webpage, 'title')

        display_id = video_id
        video_id = self._search_regex(r'(?s)<video\b[^>]+\bdata-id\s*=\s*["\']?([\w-]+)', webpage, 'short video ID')
        srcs = self._download_json(
            f'https://www.{domain}/v-alt/{video_id}', video_id,
            note='Downloading list of source files')

        formats = []
        for k, v in srcs.items():
            f_url = url_or_none(v)
            if not f_url:
                continue

            height = self._search_regex(r'^data-src(\d{3,})$', k, 'height', default=None)
            if not height:
                continue

            formats.append({
                'url': f_url,
                'format_id': height,
                'height': int_or_none(height),
            })

        if not formats:
            formats = [{'url': url} for url in srcs.values()]

        info = self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={})
        info.pop('url', None)

        # may not have found the thumbnail if it was in a list in the ld+json
        info.setdefault('thumbnail', self._og_search_thumbnail(webpage))
        detail = (get_element_by_class('detail-video-block', webpage)
                  or get_element_by_class('detail-block', webpage) or '')
        info['description'] = self._html_search_regex(
            rf'(?s)(.+?)(?:{re.escape(info.get("description", ""))}\s*<|<ul\b)',
            detail, 'description', default=None) or None
        info['title'] = re.sub(r'\s*[,-][^,-]+$', '', info.get('title') or title) or self._generic_title(url)

        def cat_tags(name, html):
            l = self._html_search_regex(
                rf'(?s)<span\b[^>]*>\s*{re.escape(name)}\s*:\s*</span>(.+?)</li>',
                html, name, default='')
            return list(filter(None, re.split(r'\s+', l)))

        return merge_dicts({
            'id': video_id,
            'display_id': display_id,
            'age_limit': 18,
            'formats': formats,
            'categories': cat_tags('Categories', detail),
            'tags': cat_tags('Tags', detail),
            'uploader': self._html_search_regex(r'[Uu]ploaded\s+by\s(.+?)"', webpage, 'uploader', default=None),
        }, info)