def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        preloaded_state = self._search_json(r'__PRELOADED_STATE__\s*=', webpage, 'preloaded state', video_id)

        content_id = traverse_obj(
            preloaded_state, ('articleDetail', 'paragraphs', ..., 'objectItems', ..., 'video', 'vid'),
            get_all=False, expected_type=int)
        if content_id is None:
            raise ExtractorError('This article does not contain a video', expected=True)

        HOST = 'news.yahoo.co.jp'
        space_id = traverse_obj(preloaded_state, ('pageData', 'spaceId'), expected_type=str)
        json_data = self._download_json(
            f'https://feapi-yvpub.yahooapis.jp/v1/content/{content_id}',
            video_id, query={
                'appid': 'dj0zaiZpPVZMTVFJR0FwZWpiMyZzPWNvbnN1bWVyc2VjcmV0Jng9YjU-',
                'output': 'json',
                'domain': HOST,
                'ak': hashlib.md5('_'.join((space_id, HOST)).encode()).hexdigest() if space_id else '',
                'device_type': '1100',
            })

        title = (
            traverse_obj(preloaded_state,
                         ('articleDetail', 'headline'), ('pageData', 'pageParam', 'title'),
                         expected_type=str)
            or self._html_search_meta(('og:title', 'twitter:title'), webpage, 'title', default=None)
            or self._html_extract_title(webpage))
        description = (
            traverse_obj(preloaded_state, ('pageData', 'description'), expected_type=str)
            or self._html_search_meta(
                ('og:description', 'description', 'twitter:description'),
                webpage, 'description', default=None))
        thumbnail = (
            traverse_obj(preloaded_state, ('pageData', 'ogpImage'), expected_type=str)
            or self._og_search_thumbnail(webpage, default=None)
            or self._html_search_meta('twitter:image', webpage, 'thumbnail', default=None))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': self._extract_formats(json_data, video_id),
        }