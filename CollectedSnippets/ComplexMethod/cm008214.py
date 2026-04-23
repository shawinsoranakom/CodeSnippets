def _fetch_page(self, album_id, hashed_pass, is_embed, referer, page):
        api_page = page + 1
        query = {
            **self._get_embed_params(is_embed, referer),
            'fields': 'link,uri',
            'page': api_page,
            'per_page': self._PAGE_SIZE,
        }
        if hashed_pass:
            query['_hashed_pass'] = hashed_pass
        try:
            videos = self._download_json(
                f'https://api.vimeo.com/albums/{album_id}/videos',
                album_id, f'Downloading page {api_page}', query=query, headers={
                    'Authorization': 'jwt ' + self._fetch_viewer_info(album_id)['jwt'],
                    'Accept': 'application/json',
                })['data']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                return
            raise
        for video in videos:
            link = video.get('link')
            if not link:
                continue
            uri = video.get('uri')
            video_id = self._search_regex(r'/videos/(\d+)', uri, 'id', default=None) if uri else None
            if is_embed:
                if not video_id:
                    self.report_warning(f'Skipping due to missing video ID: {link}')
                    continue
                link = f'https://player.vimeo.com/video/{video_id}'
                if referer:
                    link = self._smuggle_referrer(link, referer)
            yield self.url_result(link, VimeoIE.ie_key(), video_id)