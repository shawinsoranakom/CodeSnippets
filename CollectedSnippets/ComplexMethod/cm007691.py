def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site = mobj.group('site') or mobj.group('site_t')
        video_id = mobj.group('id')

        self._login(site)

        prefixed = url.startswith(self._URL_PREFIX)
        if prefixed:
            url = url[len(self._URL_PREFIX):]

        webpage = self._download_webpage(url, video_id)

        wistia_urls = WistiaIE._extract_urls(webpage)
        if not wistia_urls:
            if any(re.search(p, webpage) for p in (
                    r'class=["\']lecture-contents-locked',
                    r'>\s*Lecture contents locked',
                    r'id=["\']lecture-locked',
                    # https://academy.tailoredtutors.co.uk/courses/108779/lectures/1955313
                    r'class=["\'](?:inner-)?lesson-locked',
                    r'>LESSON LOCKED<')):
                self.raise_login_required('Lecture contents locked')
            raise ExtractorError('Unable to find video URL')

        title = self._og_search_title(webpage, default=None)

        chapter = None
        chapter_number = None
        section_item = self._search_regex(
            r'(?s)(?P<li><li[^>]+\bdata-lecture-id=["\']%s[^>]+>.+?</li>)' % video_id,
            webpage, 'section item', default=None, group='li')
        if section_item:
            chapter_number = int_or_none(self._search_regex(
                r'data-ss-position=["\'](\d+)', section_item, 'section id',
                default=None))
            if chapter_number is not None:
                sections = []
                for s in re.findall(
                        r'(?s)<div[^>]+\bclass=["\']section-title[^>]+>(.+?)</div>', webpage):
                    section = strip_or_none(clean_html(s))
                    if not section:
                        sections = []
                        break
                    sections.append(section)
                if chapter_number <= len(sections):
                    chapter = sections[chapter_number - 1]

        entries = [{
            '_type': 'url_transparent',
            'url': wistia_url,
            'ie_key': WistiaIE.ie_key(),
            'title': title,
            'chapter': chapter,
            'chapter_number': chapter_number,
        } for wistia_url in wistia_urls]

        return self.playlist_result(entries, video_id, title)