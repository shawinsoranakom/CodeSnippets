def _real_extract(self, url):
        host, album_id, name, channel_id, tag_id, mode1, mode2, mode3 = self._match_valid_url(url).group(
            'host', 'album_id', 'name', 'channel_id', 'tag_id', 'mode1', 'mode2', 'mode3')

        mode = mode1 or mode2 or mode3
        playlist_id = album_id or channel_id or tag_id

        webpage = self._download_webpage(url, playlist_id, fatal=False) or ''
        title = (self._html_search_meta('title', webpage, fatal=False)
                 or self._html_extract_title(webpage))

        url_part = (f'aid/{album_id}' if album_id
                    else f'category/{name}/category_id/{channel_id}' if mode == 'category'
                    else f'title/{name}/channel/{channel_id}' if mode == 'channel'
                    else f'tag/{tag_id}')

        data = {
            'vars[mode]': mode,
            f'vars[{mode}]': playlist_id,
            'vars[context]': '4' if album_id else '1' if mode == 'category' else '3' if mode == 'album' else '0',
            'vars[context_id]': playlist_id,
            'vars[layout]': 'thumb',
            'vars[per_page][thumb]': str(self._PAGE_SIZE),
        }

        return self.playlist_result(
            OnDemandPagedList(functools.partial(
                self._fetch_page, host, url_part, playlist_id, data), self._PAGE_SIZE),
            playlist_title=title, id=f'{mode}-{playlist_id}')