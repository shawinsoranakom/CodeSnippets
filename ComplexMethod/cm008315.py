def _real_extract(self, url):
        page_id = self._match_id(url)

        if mobj := re.fullmatch(self._VIDEO_ID_RE, urllib.parse.urlparse(url).fragment):
            page_id = mobj.group('id')

        if re.fullmatch(self._VIDEO_ID_RE, page_id):
            return self._ninecninemedia_url_result(page_id)

        webpage = self._download_webpage(f'https://www.ctvnews.ca/{page_id}', page_id, query={
            'ot': 'example.AjaxPageLayout.ot',
            'maxItemsPerPage': 1000000,
        })
        entries = [self._ninecninemedia_url_result(clip_id)
                   for clip_id in orderedSet(re.findall(r'clip\.id\s*=\s*(\d+);', webpage))]
        if not entries:
            webpage = self._download_webpage(url, page_id)
            if 'getAuthStates("' in webpage:
                entries = [self._ninecninemedia_url_result(clip_id) for clip_id in
                           self._search_regex(r'getAuthStates\("([\d+,]+)"', webpage, 'clip ids').split(',')]
            else:
                entries = [
                    self._ninecninemedia_url_result(clip_id) for clip_id in
                    traverse_obj(webpage, (
                        {find_element(tag='jasper-player-container', html=True)},
                        {extract_attributes}, 'axis-ids', {json.loads}, ..., 'axisId', {str}))
                ]

        return self.playlist_result(entries, page_id)