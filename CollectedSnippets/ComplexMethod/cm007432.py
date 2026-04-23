def _entries(self, url, pl_id, html=None, page_num=None):

        # separates page sections
        PLAYLIST_SECTION_RE = (
            r'''<div\s[^>]*\bclass\s*=\s*('|")(?:[\w$-]+\s+|\s)*?title-bar(?:\s+[\w$-]+|\s)*\1[^>]*>'''
        )
        # contains video link
        VIDEO_URL_RE = r'''(?x)
            <div\s[^>]*\bdata-video-id\s*=\s*('|")\d+\1[^>]*>\s*
            (?:<div\b[\s\S]+?</div>\s*)*
            <a\s[^>]*\bhref\s*=\s*('|")(?P<url>(?:(?!\2)[^>])+)\2
        '''

        def yield_pages(url, html=html, page_num=page_num):
            fatal = not html
            for pnum in itertools.count(start=page_num or 1):
                if not html:
                    html = self._download_webpage(
                        url, pl_id, note='Downloading page %d' % pnum,
                        fatal=fatal)
                if not html:
                    break
                fatal = False
                yield (url, html, pnum)
                # explicit page: extract just that page
                if page_num is not None:
                    break
                next_url = self._get_next_url(url, pl_id, html)
                if not next_url or next_url == url:
                    break
                url, html = next_url, None

        def retry_page(msg, tries_left, page_data):
            if tries_left <= 0:
                return
            self.report_warning(msg, pl_id)
            sleep(self._PAGE_RETRY_DELAY)
            return next(
                yield_pages(page_data[0], page_num=page_data[2]), None)

        def yield_entries(html):
            for frag in re.split(PLAYLIST_SECTION_RE, html):
                if not frag:
                    continue
                t_text = get_element_by_class('title-text', frag or '')
                if not (t_text and re.search(self._PLAYLIST_TITLEBAR_RE, t_text)):
                    continue
                for m in re.finditer(VIDEO_URL_RE, frag):
                    video_url = urljoin(url, m.group('url'))
                    if video_url:
                        yield self.url_result(video_url)

        last_first_url = None
        for page_data in yield_pages(url, html=html, page_num=page_num):
            # page_data: url, html, page_num
            first_url = None
            tries_left = self._PAGE_RETRY_COUNT + 1
            while tries_left > 0:
                tries_left -= 1
                for from_ in yield_entries(page_data[1]):
                    # may get the same page twice instead of empty page
                    # or (site bug) intead of actual next page
                    if not first_url:
                        first_url = from_['url']
                        if first_url == last_first_url:
                            # sometimes (/porntags/) the site serves the previous page
                            # instead but may provide the correct page after a delay
                            page_data = retry_page(
                                'Retrying duplicate page...', tries_left, page_data)
                            if page_data:
                                first_url = None
                                break
                            continue
                    yield from_
                else:
                    if not first_url and 'no-result-paragarph1' in page_data[1]:
                        page_data = retry_page(
                            'Retrying empty page...', tries_left, page_data)
                        if page_data:
                            continue
                    else:
                        # success/failure
                        break
            # may get an infinite (?) sequence of empty pages
            if not first_url:
                break
            last_first_url = first_url