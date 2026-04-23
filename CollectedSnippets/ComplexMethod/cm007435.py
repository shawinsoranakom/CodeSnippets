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