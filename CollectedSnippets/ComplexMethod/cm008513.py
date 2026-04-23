def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        site = mobj.group('site') or mobj.group('site_t')
        course_id = mobj.group('id')

        self._login(site)

        prefixed = url.startswith(self._URL_PREFIX)
        if prefixed:
            prefix = self._URL_PREFIX
            url = url[len(prefix):]

        webpage = self._download_webpage(url, course_id)

        url_base = f'https://{site}/'

        entries = []

        for mobj in re.finditer(
                r'(?s)(?P<li><li[^>]+class=(["\'])(?:(?!\2).)*?section-item[^>]+>.+?</li>)',
                webpage):
            li = mobj.group('li')
            if 'fa-youtube-play' not in li and not re.search(r'\d{1,2}:\d{2}', li):
                continue
            lecture_url = self._search_regex(
                r'<a[^>]+href=(["\'])(?P<url>(?:(?!\1).)+)\1', li,
                'lecture url', default=None, group='url')
            if not lecture_url:
                continue
            lecture_id = self._search_regex(
                r'/lectures/(\d+)', lecture_url, 'lecture id', default=None)
            title = self._html_search_regex(
                r'<span[^>]+class=["\']lecture-name[^>]+>([^<]+)', li,
                'title', default=None)
            entry_url = urljoin(url_base, lecture_url)
            if prefixed:
                entry_url = self._URL_PREFIX + entry_url
            entries.append(
                self.url_result(
                    entry_url,
                    ie=TeachableIE.ie_key(), video_id=lecture_id,
                    video_title=clean_html(title)))

        course_title = self._html_search_regex(
            (r'(?s)<img[^>]+class=["\']course-image[^>]+>\s*<h\d>(.+?)</h',
             r'(?s)<h\d[^>]+class=["\']course-title[^>]+>(.+?)</h'),
            webpage, 'course title', fatal=False)

        return self.playlist_result(entries, course_id, course_title)