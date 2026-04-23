def _fetch_page(self, album_id, authorization, hashed_pass, page):
        api_page = page + 1
        query = {
            'fields': 'link,uri',
            'page': api_page,
            'per_page': self._PAGE_SIZE,
        }
        if hashed_pass:
            query['_hashed_pass'] = hashed_pass
        try:
            videos = self._download_json(
                'https://api.vimeo.com/albums/%s/videos' % album_id,
                album_id, 'Downloading page %d' % api_page, query=query, headers={
                    'Authorization': 'jwt ' + authorization,
                })['data']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                return
        for video in videos:
            link = video.get('link')
            if not link:
                continue
            uri = video.get('uri')
            video_id = self._search_regex(r'/videos/(\d+)', uri, 'video_id', default=None) if uri else None
            yield self.url_result(link, VimeoIE.ie_key(), video_id)