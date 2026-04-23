def _entries(self, url, host, item_id):
        page = self._extract_page(url)

        VIDEOS = '/videos'

        def download_page(base_url, num, fallback=False):
            note = 'Downloading page {}{}'.format(num, ' (switch to fallback)' if fallback else '')
            return self._download_webpage(
                base_url, item_id, note, query={'page': num})

        def is_404(e):
            return isinstance(e.cause, HTTPError) and e.cause.status == 404

        base_url = url
        has_page = page is not None
        first_page = page if has_page else 1
        for page_num in (first_page, ) if has_page else itertools.count(first_page):
            try:
                try:
                    webpage = download_page(base_url, page_num)
                except ExtractorError as e:
                    # Some sources may not be available via /videos page,
                    # trying to fallback to main page pagination (see [1])
                    # 1. https://github.com/ytdl-org/youtube-dl/issues/27853
                    if is_404(e) and page_num == first_page and VIDEOS in base_url:
                        base_url = base_url.replace(VIDEOS, '')
                        webpage = download_page(base_url, page_num, fallback=True)
                    else:
                        raise
            except ExtractorError as e:
                if is_404(e) and page_num != first_page:
                    break
                raise
            page_entries = self._extract_entries(webpage, host)
            if not page_entries:
                break
            yield from page_entries
            if not self._has_more(webpage):
                break