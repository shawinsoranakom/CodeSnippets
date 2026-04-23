def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        if mobj is None:
            raise ExtractorError(f'Invalid URL: {url}')
        series_id = mobj.group('id')
        fragment = urllib.parse.urlparse(url).fragment

        webpage_url = f'https://w.duboku.io/voddetail/{series_id}.html'
        webpage_html = self._download_webpage(webpage_url, series_id)

        # extract title

        title = _get_element_by_tag_and_attrib(webpage_html, 'h1', 'class', 'title')
        title = unescapeHTML(title.group('content')) if title else None
        if not title:
            title = self._html_search_meta('keywords', webpage_html)
        if not title:
            title = _get_element_by_tag_and_attrib(webpage_html, 'title')
            title = unescapeHTML(title.group('content')) if title else None

        # extract playlists

        playlists = {}
        for div in _get_elements_by_tag_and_attrib(
                webpage_html, attribute='id', value='playlist\\d+', escape_value=False):
            playlist_id = div.group('value')
            playlist = []
            for a in _get_elements_by_tag_and_attrib(
                    div.group('content'), 'a', 'href', value='[^\'"]+?', escape_value=False):
                playlist.append({
                    'href': unescapeHTML(a.group('value')),
                    'title': unescapeHTML(a.group('content')),
                })
            playlists[playlist_id] = playlist

        # select the specified playlist if url fragment exists
        playlist = None
        playlist_id = None
        if fragment:
            playlist = playlists.get(fragment)
            playlist_id = fragment
        else:
            first = next(iter(playlists.items()), None)
            if first:
                (playlist_id, playlist) = first
        if not playlist:
            raise ExtractorError(
                f'Cannot find {fragment}' if fragment else 'Cannot extract playlist')

        # return url results
        return self.playlist_result([
            self.url_result(
                urllib.parse.urljoin('https://w.duboku.io', x['href']),
                ie=DubokuIE.ie_key(), video_title=x.get('title'))
            for x in playlist], series_id + '#' + playlist_id, title)