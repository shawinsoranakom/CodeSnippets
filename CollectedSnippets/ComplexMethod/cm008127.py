def _entries(self, url, pl_id, html=None, page_num=None):
        start = page_num or 1
        for page in itertools.count(start):
            if not html:
                html = self._download_webpage(
                    url, pl_id, note=f'Downloading page {page}', fatal=page == start)
            if not html:
                return
            for element in get_elements_html_by_class('video-title', html):
                if video_url := traverse_obj(element, ({extract_attributes}, 'href', {urljoin(url)})):
                    yield self.url_result(video_url)

            if page_num is not None:
                return
            next_url = self._get_next_url(url, pl_id, html)
            if not next_url or next_url == url:
                return
            url = next_url
            html = None