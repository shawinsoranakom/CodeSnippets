def _real_extract(self, url):
        list_id = self._match_id(url)

        bvid = traverse_obj(parse_qs(url), ('bvid', 0))
        if not self._yes_playlist(list_id, bvid):
            return self.url_result(f'https://www.bilibili.com/video/{bvid}', BiliBiliIE)

        webpage = self._download_webpage(url, list_id)
        initial_state = self._search_json(r'window\.__INITIAL_STATE__\s*=', webpage, 'initial state', list_id)
        error = traverse_obj(initial_state, (('error', 'listError'), all, lambda _, v: v['code'], any))
        if error and error['code'] != 200:
            error_code = error.get('trueCode')
            if error_code == -400 and list_id == 'watchlater':
                self.raise_login_required('You need to login to access your watchlater playlist')
            elif error_code == -403:
                self.raise_login_required('This is a private playlist. You need to login as its owner')
            elif error_code == 11010:
                raise ExtractorError('Playlist is no longer available', expected=True)
            raise ExtractorError(f'Could not access playlist: {error_code} {error.get("message")}')

        query = {
            'ps': 20,
            'with_current': False,
            **traverse_obj(initial_state, {
                'type': ('playlist', 'type', {int_or_none}),
                'biz_id': ('playlist', 'id', {int_or_none}),
                'tid': ('tid', {int_or_none}),
                'sort_field': ('sortFiled', {int_or_none}),
                'desc': ('desc', {bool_or_none}, {str_or_none}, {str.lower}),
            }),
        }
        metadata = {
            'id': f'{query["type"]}_{query["biz_id"]}',
            **traverse_obj(initial_state, ('mediaListInfo', {
                'title': ('title', {str}),
                'uploader': ('upper', 'name', {str}),
                'uploader_id': ('upper', 'mid', {str_or_none}),
                'timestamp': ('ctime', {int_or_none}, filter),
                'thumbnail': ('cover', {url_or_none}),
            })),
        }
        return self.playlist_result(self._extract_medialist(query, list_id), **metadata)